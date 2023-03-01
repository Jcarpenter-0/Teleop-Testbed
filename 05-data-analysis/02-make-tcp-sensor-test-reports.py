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
Tests = glob.glob('../../../Analysis/*-Datasets-*/')
Tests.sort(reverse=True)
TestsDataDF = pd.read_csv('../../../Analysis/tests.csv')
TmpDirectory = '../../../Datasets/tmp/'
AnalysisDir = '../../../Analysis/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
SensorSendPorts = ['4002','4003','4004','4005']
OperatorLabel = 'net.interface.cellular[].homeoperator'
# =============================================================

macroReport = pd.DataFrame()
macroRTTDataDF = pd.DataFrame()

for testNum, testDir in enumerate(Tests):
    testID = int(testDir.split('/')[-2].split('--')[0])

    print('Test {}/{} in {}'.format(testID, len(Tests)-1, testDir))

    reportDF = pd.DataFrame()

    for sensorPort in SensorSendPorts:

        try:

            sensorData = pd.read_csv(testDir + 'sensor-{}-data.csv'.format(sensorPort))

            sensorRowDF = pd.DataFrame()

            testDuration = float(TestsDataDF[TestsDataDF['TestID'] == testID]['Actual-Test-Duration (seconds)'].values[0])

            sensorTputBps = (sensorData['Length-Of-Chunk-Received(Bytes)'].sum() * 8)/testDuration
            try:
                sensorAttemptedTputBps = (sensorData['PacketSendSize(Bytes)'].sum() * 8)/testDuration
            except:
                print('Missing "PacketSendSize(Bytes)')
                sensorAttemptedTputBps = None

            sizeBeforeDrop = len(sensorData)
            droppedPackets = sensorData[sensorData['Length-Of-Chunk-Received(Bytes)'].isna()]
            sentPackets = sensorData.dropna(subset=['Length-Of-Chunk-Received(Bytes)'])

            totalPartIDs = set(sensorData['PartID'].unique())
            sentPartIDs = set(sentPackets['PartID'].unique())
            droppedPartIDs = set(droppedPackets['PartID'].unique())
            actuallyTransmittedParts = sentPartIDs.difference(droppedPartIDs)

            partLossPercent = 1-(len(actuallyTransmittedParts)/len(totalPartIDs))

            totalObvs = set(sensorData['ObvservationID'].unique())
            sentObvs = set(sentPackets['ObvservationID'].unique())
            droppedObvs = set(droppedPackets['ObvservationID'].unique())
            actuallyTransmittedObvs = sentObvs.difference(droppedObvs)

            obvLostPercent = 1-len(actuallyTransmittedObvs)/len(totalObvs)

            sensorRowDF['Test-ID'] = [testID]
            sensorRowDF['Sensor'] = [sensorPort]
            sensorRowDF['Carrier'] = [sensorData[OperatorLabel].unique()]

            # Get the wireshark based data
            retransmitFiles = glob.glob(testDir + '{}-retransmits.csv'.format(sensorPort))
            rttFiles = glob.glob(testDir + '{}-rtts.csv'.format(sensorPort))

            if len(retransmitFiles) > 0:
                retransmitsDF = pd.read_csv(retransmitFiles[0], header=None)
                sensorRowDF['TCP-Retransmits'] = [len(retransmitsDF)]
            else:
                sensorRowDF['TCP-Retransmits'] = [0]

            if len(rttFiles) > 0:
                rttFileDF = pd.read_csv(rttFiles[0], header=None)

                rttFileDF['Test-ID'] = [testID] * len(rttFileDF)
                rttFileDF['Sensor'] = [sensorPort] * len(rttFileDF)
                rttFileDF['Carrier'] = [sensorData[OperatorLabel].unique()] * len(rttFileDF)

                macroRTTDataDF = pd.concat([macroRTTDataDF, rttFileDF])


                sensorRowDF['TCP-Initial-RTT(S)'] = [rttFileDF[1].values[-1]]
                sensorRowDF['TCP-RTT(S)-AVG'] = [rttFileDF[2].mean()]
                sensorRowDF['TCP-RTT(S)-STD'] = [rttFileDF[2].std()]
                sensorRowDF['TCP-Lat(S)-Est'] = [rttFileDF[2].mean()/2]


            # QoS
            sensorRowDF['Attempt Throughput (bps)'] = [sensorAttemptedTputBps]
            sensorRowDF['Goodput Throughput (bps)'] = [sensorTputBps]
            sensorRowDF['Part-Loss (%)'] = [partLossPercent]

            # QoE esque
            sensorRowDF['Observation-Loss (%)'] = [obvLostPercent]
            sensorRowDF['Observations-per-second'] = [(len(actuallyTransmittedObvs)/testDuration)]

            reportDF = pd.concat([reportDF, sensorRowDF])

            macroReport = pd.concat([macroReport, sensorRowDF])

        except Exception as ex:
            print(ex)
            print('Issue reading in sensor data, may not be in this test')

    if len(reportDF) > 0:
        reportDF.to_csv(testDir + 'tcp-sensor-test-report.csv', index=False)

macroReport.to_csv(AnalysisDir + 'macro-tcp-sensor-test-report.csv', index=False)
macroRTTDataDF.to_csv(AnalysisDir + 'macro-tcp-sensor-rtt-data.csv', index=False)






