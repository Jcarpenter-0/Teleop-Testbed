import glob
import pandas as pd
import numpy as np
import json
import shutil
import os
import datetime
import subprocess
from datetime import datetime, timedelta
from pytimeparse.timeparse import timeparse
import zlib

# =============================================================
# Go through each test folder and produce some readable files for use
# =============================================================

ClientTestDirs = glob.glob('../../../Datasets/client-data/test-dir/output/*/')
ServerTestDirs = glob.glob('../../../Datasets/server-data/test-dir/output/*/')
TmpDirectory = '../../../Datasets/tmp/'
DataOutputDir = './output/'
DataInputDir = './input/'
AnalysisDir = '../../../Analysis/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
SensorSendPorts = ['2379','2380','2381','8319','8320','8321']
TcpSendPorts = ['4000','4001','4002','4003','4004','4005']

ClientTestDirs.sort(reverse=True)
ServerTestDirs.sort(reverse=True)

ProduceCameraMicroReport = False
ProduceLiDARMicroReport = True
ProduceTCPSensorReport = False

# =============================================================
# Globals
SensorMicroReportDF = pd.DataFrame()
TCPSensorMicroReportDF = pd.DataFrame()
CameraMicroReportDF = pd.DataFrame()
TestsReportDF = pd.DataFrame()

# =============================================================
# For each test, make a new directory and populate it with pieces of data analysis

for testID, clientTestDir in enumerate(ClientTestDirs):
    serverTestDir = ServerTestDirs[testID]
    print('{}/{} - Started {} - {}'.format(testID + 1, len(ClientTestDirs), clientTestDir, serverTestDir))
    targetTestDir = AnalysisDir + '/{}-{}/'.format(testID,serverTestDir.replace('/','-').replace('.','-'))
    os.makedirs(targetTestDir, exist_ok=True)

    # Do meta test work
    testMetaFP = open(clientTestDir + 'Test-Information.json', 'r')
    testMetaData = json.load(testMetaFP)
    testMetaFP.close()

    #mfrDF = pd.read_csv(clientTestDir + 'xr90-mobile-logs.csv')
    mfrDF = pd.DataFrame()

    # Modify the MFR sightly (for later merging with tput files)
    #mfrDF['Merge-Date-Epoch'] = np.trunc(mfrDF['Log-Date-Time-Epoch'])
    #firstRow = mfrDF.head(1)
    #lastRow = mfrDF.tail(1)

    #actualTestDuration = float(lastRow['Log-Date-Time-Epoch'].values[0]) - float(firstRow['Log-Date-Time-Epoch'].values[0])
    actualTestDuration = 0

    testReportRow = pd.DataFrame()
    testReportRow['TestID'] = [testID]
    testReportRow['Test-Date'] = [testMetaData["Test-Start-Timestamp"]]
    testReportRow['Set-Test-Duration (seconds)'] = [testMetaData["Test-Duration-Seconds"]]
    testReportRow['Actual-Test-Duration (seconds)'] = [actualTestDuration]
    testReportRow['Number-Of-Cameras'] = [testMetaData["Number-Of-Cameras"]]
    testReportRow['Number-Of-LiDARs'] = [testMetaData["Number-Of-LiDARs"]]
    testReportRow['Number-Of-Other-Sensors'] = [testMetaData["Number-Of-Iperfs"]]
    testReportRow['Client-Dir'] = [clientTestDir]
    testReportRow['Server-Dir'] = [serverTestDir]

    TestsReportDF = pd.concat([TestsReportDF, testReportRow])

    # Do Camera Work
    if ProduceCameraMicroReport:
        cameraFrameFiles = glob.glob(serverTestDir + 'camera-*-frames.csv')

        for cameraFile in cameraFrameFiles:
            # Combine MFR with sensor file
            cameraName = cameraFile.split('/')[-1].replace('-frames.csv','')

            cameraFileDF = pd.read_csv(cameraFile)
            cameraFileDF['Merge-Date-Epoch'] = np.trunc(cameraFileDF['Frame-Epoch-Timestamp'])

            mergedDF = pd.merge(cameraFileDF, mfrDF, how='outer', on='Merge-Date-Epoch')
            mergedDF['Test-ID'] = testID
            mergedDF['Sensor-ID'] = cameraName

            mergedDF.to_csv(targetTestDir + '{}-data.csv'.format(cameraName), index=False)

            CameraMicroReportDF = pd.concat([CameraMicroReportDF, mergedDF])

    # Do Sensor Work
    # Combine the client-server timings
    if ProduceLiDARMicroReport:
        for senderPort in SensorSendPorts:

            clientAppSenderLog = glob.glob(clientTestDir + 'sensor-*-{}-logs.csv'.format(senderPort))
            serverAppSenderLog = glob.glob(serverTestDir + '{}-post-process-logs.csv'.format(senderPort))

            if len(clientAppSenderLog) > 0 and len(serverAppSenderLog) > 0:
                clientDF = pd.read_csv(clientAppSenderLog[0])
                serverDF = pd.read_csv(serverAppSenderLog[0])

                try:

                    # prepare the timestamps on client side for sending (may replace later if updated client code)
                    clientDF['Send-Timestamp-Obj'] = pd.to_datetime(clientDF['Send-Timestamp'], format=DateTimeFormat)

                    # Need to parse the
                    serverDF['Recv-Timestamp-Obj'] = pd.to_datetime(serverDF['Receive-Timestamp(s)'], format=DateTimeFormat)

                    mergedClientServerDF = pd.merge(clientDF, serverDF, how='outer', on='PartID')

                    mergedClientServerDF['Send-Receive-Timings (Seconds)'] = mergedClientServerDF.apply(
                        lambda row: (row['Recv-Timestamp-Obj'] - row['Send-Timestamp-Obj']).total_seconds(), axis=1)

                    # Merge the MFR
                    mergedClientServerDF['Merge-Date-Epoch'] = np.trunc(mergedClientServerDF['Send-Timestamp-Epoch'])
                    #mergedDF = pd.merge(mergedClientServerDF, mfrDF, how='outer', on='Merge-Date-Epoch')
                    mergedDF = mergedClientServerDF
                    # Drop columns to save space
                    #mergedDF = mergedDF.drop(columns=['Location-Text','net.interface.cellular[].service','Network Sent',
                    #    'TagLength(Bytes)', 'Recv-Timestamp-Obj', 'net.interface.cellular[].msim.activeslot',
                    #                                   'net.interface.cellular[].roamingstring','net.interface.cellular[].iccid','net.interface.cellular[].lac','Compression Time (microseconds)','Raw Obv Size(bytes)','Send-Timestamp-Obj'],
                    #                          axis=1)

                    mergedDF['Test-ID'] = testID
                    mergedDF['Sensor-ID'] = senderPort

                    mergedDF.to_csv(targetTestDir + 'sensor-{}-data.csv'.format(senderPort), index=False)

                    # Select a subset of the data to go to the macroreport
                    rowNthSample = int(len(mergedDF) * 0.0001)

                    subsetMergedDF = mergedDF.iloc[::rowNthSample, :]

                    SensorMicroReportDF = pd.concat([SensorMicroReportDF, subsetMergedDF])

                except Exception as ex:
                    print('Issue with {} {} {}'.format(serverTestDir, senderPort, ex))

    if ProduceTCPSensorReport:
        for senderPort in TcpSendPorts:

            clientAppSenderLog = glob.glob(clientTestDir + 'sensor-*-{}-logs.csv'.format(senderPort))
            serverAppSenderLog = glob.glob(serverTestDir + '{}-post-process-logs.csv'.format(senderPort))


            filesToMove = glob.glob(clientTestDir + 'throughputs.csv')
            filesToMove.extend(glob.glob(clientTestDir + '*-retransmits.csv'))
            filesToMove.extend(glob.glob(clientTestDir + '*-rtts.csv'))

            for file in filesToMove:
                if os.path.getsize(file) > 0:
                    fileName = os.path.basename(file)
                    shutil.move(file, targetTestDir + fileName)
                else:
                    os.remove(file)


            if len(clientAppSenderLog) > 0 and len(serverAppSenderLog) > 0:
                clientDF = pd.read_csv(clientAppSenderLog[0])
                serverDF = pd.read_csv(serverAppSenderLog[0])

                try:

                    mergedClientServerDF = pd.merge(clientDF, serverDF, how='outer', on='PartID')

                    # Merge the MFR
                    mergedClientServerDF['Merge-Date-Epoch'] = np.trunc(mergedClientServerDF['Send-Timestamp-Epoch'])
                    mergedDF = pd.merge(mergedClientServerDF, mfrDF, how='outer', on='Merge-Date-Epoch')
                    # Drop columns to save space
                    mergedDF = mergedDF.drop(columns=['Location-Text','net.interface.cellular[].service','Network Sent',
                        'TagLength(Bytes)','net.interface.cellular[].msim.activeslot',
                                                       'net.interface.cellular[].roamingstring','net.interface.cellular[].iccid','net.interface.cellular[].lac','Compression Time (microseconds)','Raw Obv Size(bytes)'],
                                              axis=1)

                    mergedDF['Test-ID'] = testID
                    mergedDF['Sensor-ID'] = senderPort

                    mergedDF.to_csv(targetTestDir + 'sensor-{}-data.csv'.format(senderPort), index=False)

                    # Select a subset of the data to go to the macroreport
                    rowNthSample = int(len(mergedDF) * 0.0001)

                    subsetMergedDF = mergedDF.iloc[::rowNthSample, :]

                    TCPSensorMicroReportDF = pd.concat([TCPSensorMicroReportDF, subsetMergedDF])

                except Exception as ex:
                    print('Issue with {} {} {}'.format(serverTestDir, senderPort, ex))


TestsReportDF.to_csv(AnalysisDir + 'tests.csv', index=False)
if ProduceLiDARMicroReport:
    SensorMicroReportDF.to_csv(AnalysisDir + 'udp-sensor-results.csv', index=False)
if ProduceCameraMicroReport:
    CameraMicroReportDF.to_csv(AnalysisDir + 'camera-results.csv', index=False)
if ProduceTCPSensorReport:
    TCPSensorMicroReportDF.to_csv(AnalysisDir + 'tcp-sensor-results.csv', index=False)
