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
import glob

# =============================================================
# Go through each test folder and produce some readable files for use
# =============================================================
Tests = glob.glob('../../../Analysis/0----------Datasets-server-data-test-dir-output-Server-23-06-27-04-06-27-886661-cubic-/')
# 0----------Datasets-server-data-test-dir-output-Server-23-06-27-04-06-27-886661-cubic-
# '../../../Analysis/*-Datasets-*/'
Tests.sort()
TestsDataDF = pd.read_csv('../../../Analysis/tests.csv')
TmpDirectory = '../../../Datasets/tmp/'
AnalysisDir = '../../../Analysis/'
ApplicationSpecificsDF = pd.read_csv('../../../Datasets/sensor-inputs/Velodyne-lidar-puck-16/azimuths.csv')
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
SensorSendPorts = ['2380']
# '2379','2380','2381','8319','8320','8321'

OperatorLabel = 'net.interface.cellular[].homeoperator'


# =============================================================

macroReport = pd.DataFrame()

for testNum, testDir in enumerate(Tests):

    testID = int(testDir.split('/')[-2].split('--')[0])

    print('Test {}/{} in {}'.format(testID, len(Tests)-1, testDir))

    reportDF = pd.DataFrame()

    for sensorPort in SensorSendPorts:

        try:
            sensorDataBase = pd.read_csv(testDir + 'sensor-{}-data.csv'.format(sensorPort))

            sensorData = pd.merge(sensorDataBase, ApplicationSpecificsDF, how='outer', on='ObvservationID')

            sensorRowDF = pd.DataFrame()

            testDuration = float(TestsDataDF[TestsDataDF['TestID'] == testID]['Actual-Test-Duration (seconds)'].values[0])

            sensorTputBps = (sensorData['Length-Of-Chunk-Received(Bytes)'].sum() * 8)/testDuration
            try:
                sensorAttemptedTputBps = (sensorData['PacketSendSize(Bytes)'].sum() * 8) / testDuration
            except:
                print('Missing "PacketSendSize(Bytes)')
                sensorAttemptedTputBps = None


            sizeBeforeDrop = len(sensorData)
            sentPackets = sensorData[(sensorData['Send-Timestamp-Epoch'].isna() == False)]
            droppedPackets = sentPackets[(sensorData['Epoch-Receive-Timestamp(s)'].isna())]

            # Remove errors
            sensorData = sensorData[sensorData['Send-Receive-Timings (Seconds)'] > 0]
            # Get remaining stuff
            sentPackets = sensorData.dropna(subset=['Epoch-Receive-Timestamp(s)'])

            totalPartIDs = set(sensorData['PartID'].unique())
            sentPartIDs = set(sentPackets['PartID'].unique())
            droppedPartIDs = set(droppedPackets['PartID'].unique())
            actuallyTransmittedParts = sentPartIDs.difference(droppedPartIDs)

            partLossPercent = (len(droppedPackets)/sizeBeforeDrop)

            totalObvs = set(sensorData['ObvservationID'].unique())
            sentObvs = set(sentPackets['ObvservationID'].unique())
            droppedObvs = set(droppedPackets['ObvservationID'].unique())
            actuallyTransmittedObvs = sentObvs.difference(droppedObvs)

            obvLostPercent = 1-len(actuallyTransmittedObvs)/len(totalObvs)

            # Receive time diffs on packets that arrived
            timeBetweenPackets = sentPackets['Epoch-Receive-Timestamp(s)'].diff()

            sensorRowDF['Test-ID'] = [testID]
            sensorRowDF['Sensor'] = [sensorPort]
            #sensorRowDF['Carrier'] = [sensorData[OperatorLabel].unique()]

            # QoS
            sensorRowDF['Attempt Throughput (bps)'] = [sensorAttemptedTputBps]
            sensorRowDF['Goodput Throughput (bps)'] = [sensorTputBps]
            sensorRowDF['Packet-Loss (%)'] = [partLossPercent]
            sensorRowDF['Average-Latency (S)'] = [sensorData['Send-Receive-Timings (Seconds)'].mean()]
            sensorRowDF['Latency-STD (S)'] = [sensorData['Send-Receive-Timings (Seconds)'].std()]

            # QoE esque

            sensorRowDF['Avg Inter-Packet-Delay (S)'] = [timeBetweenPackets.mean()]
            sensorRowDF['STD Inter-Packet-Delay (S)'] = [timeBetweenPackets.std()]
            sensorRowDF['Observation-Loss (%)'] = [obvLostPercent]
            sensorRowDF['Inter-Observations-Delay (S)'] = [(testDuration/len(actuallyTransmittedObvs))]
            sensorRowDF['Observations-per-second'] = [(len(actuallyTransmittedObvs)/testDuration)]

            # Process LiDAR specific Data QoE ================================

            lidarFrameSampleDensities = []
            lidarFrameTimings = []

            currentFrameSamples = 0
            currentFrameTimings = []
            lastAzimuth = 0

            print('Doing LiDAR QoE unpacking')
            for obv in totalObvs:
                obvPieces = sentPackets[sentPackets['ObvservationID'] == obv]

                if len(obvPieces) > 0:
                    azimuthCompare = obvPieces['Azimuth'].values[-1]

                    currentFrameTimings.append(obvPieces['Epoch-Receive-Timestamp(s)'].max())

                    if lastAzimuth > azimuthCompare:
                        lidarFrameSampleDensities.append(currentFrameSamples)
                        lidarFrameTimings.append(np.max(currentFrameTimings))

                        currentFrameSamples = 0
                        currentFrameTimings.clear()

                    lastAzimuth = azimuthCompare

                    currentFrameSamples += 1


            sensorRowDF['LiDAR-Avg-Frame-Quality (Samples)'] = [np.mean(lidarFrameSampleDensities)]
            sensorRowDF['LiDAR-STD-Frame-Quality (Samples)'] = [np.std(lidarFrameSampleDensities)]
            sensorRowDF['LiDAR-FPS'] = [len(lidarFrameSampleDensities)/testDuration]
            sensorRowDF['LiDAR-AVG-Per-Frame-Time (Seconds)'] = [np.diff(lidarFrameTimings).mean()]
            sensorRowDF['LiDAR-STD-Per-Frame-Time (Seconds)'] = [np.diff(lidarFrameTimings).std()]

            # ====================================================================

            reportDF = pd.concat([reportDF, sensorRowDF])
            macroReport = pd.concat([macroReport, sensorRowDF])

        except Exception as ex:
            print(ex)
            print('Issue reading in sensor data, may not be in this test')

    if len(reportDF) > 0:
        reportDF.to_csv(testDir + 'test-report.csv', index=False)

macroReport.to_csv(AnalysisDir + 'macro-test-report.csv', index=False)






