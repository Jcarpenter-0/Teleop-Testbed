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
Tests.sort()
TestsDataDF = pd.read_csv('../../../Analysis/tests.csv')
TmpDirectory = '../../../Datasets/tmp/'
AnalysisDir = '../../../Analysis/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
OperatorLabel = 'net.interface.cellular[].homeoperator'
CameraLabels = ['camera-1','camera-2','camera-3','camera-4']
CompareFrameCounts = ['../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/output-f.mp4',
                 '../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/output-fl.mp4',
                 '../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/output-fr.mp4',
                 '../../../Datasets/sensor-inputs/Infared-Camera/output-ir.mp4']

# =============================================================

def GetVideoFrameCount(videoFile:str) -> int:

    ffprobeProc = subprocess.Popen(
        'ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames -print_format csv {}'.format(videoFile), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    ffprobeProc.wait()
    traceRaw = ffprobeProc.stdout.readlines()
    frameCount = int(traceRaw[-1].decode().replace('\n','').split(',')[-1])

    return frameCount


# =============================================================


macroReport = pd.DataFrame()

for testNum, testDir in enumerate(Tests):

    testID = int(testDir.split('/')[-2].split('--')[0])

    print('Test {}/{} in {}'.format(testID, len(Tests)-1, testDir))

    reportDF = pd.DataFrame()

    for cameraNum, cameraLabel in enumerate(CameraLabels):

        try:
            sensorData = pd.read_csv(testDir + '{}-data.csv'.format(cameraLabel))

            # Do data dropping
            sensorData = sensorData.dropna(subset=['Frame-Epoch-Timestamp'])

            sensorRowDF = pd.DataFrame()

            testDuration = float(TestsDataDF[TestsDataDF['TestID'] == testID]['Actual-Test-Duration (seconds)'].values[0])

            # Get Frame Count
            sourceVideoFrameCount = GetVideoFrameCount(CompareFrameCounts[cameraNum])

            # Get the RTT information
            rttFiles = glob.glob(testDir + '{}-*-rtts.csv'.format(cameraLabel))
            retransmitFiles = glob.glob(testDir + '{}-*-retransmits.csv'.format(cameraLabel))


            sensorRowDF['Test-ID'] = [testID]
            sensorRowDF['Sensor'] = [cameraLabel]
            sensorRowDF['Carrier'] = [sensorData[OperatorLabel].unique()]
            sensorRowDF['Source Video Frame Count'] = [sourceVideoFrameCount]
            sensorRowDF['Frames Received'] = [len(sensorData)]
            sensorRowDF['Frames Lost'] = [sourceVideoFrameCount - len(sensorData)]
            sensorRowDF['Avg-Inter-Frame-Time(S)'] = [sensorData['Inter-Frame-Times (s)'].mean()]
            sensorRowDF['Std-Inter-Frame-Time(S)'] = [sensorData['Inter-Frame-Times (s)'].std()]
            sensorRowDF['Avg-From-Stream-Start-Time(S)'] = [sensorData['Frame-Time-With-First-Frame-Delay(s)'].mean()]
            sensorRowDF['Std-From-Stream-Start-Time(S)'] = [sensorData['Frame-Time-With-First-Frame-Delay(s)'].std()]

            rttGroupDF = pd.DataFrame()
            retGroupDF = pd.DataFrame()

            for file in rttFiles:

                fileDF = pd.read_csv(file, header=None)

                rttGroupDF = pd.concat([rttGroupDF, fileDF])

            for file in retransmitFiles:

                fileDF = pd.read_csv(file, header=None)

                retGroupDF = pd.concat([retGroupDF, fileDF])


            sensorRowDF['Avg-RTT (S)'] = [rttGroupDF[2].mean()]
            sensorRowDF['STD-RTT (S)'] = [rttGroupDF[2].std()]
            sensorRowDF['Avg-Retransmits'] = [len(retransmitFiles)]

            reportDF = pd.concat([reportDF, sensorRowDF])

            macroReport = pd.concat([macroReport, sensorRowDF])

        except Exception as ex:
            print(ex)
            print('Issue reading in camera data, may not be in this test')

    if len(reportDF) > 0:
        reportDF.to_csv(testDir + 'camera-test-report.csv', index=False)

macroReport.to_csv(AnalysisDir + 'macro-camera-test-report.csv', index=False)

