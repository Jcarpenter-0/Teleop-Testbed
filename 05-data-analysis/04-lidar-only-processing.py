import glob
import pandas as pd
import datetime
import numpy as np
import subprocess

# ============================================
# Get the macro data of all the angles
# =============================================
clientSideLidarFiles = glob.glob('./04-client/output/*/lidar-client-23*-payload-compression-*-*.csv')
DateFormat = '%y-%m-%d-%H-%M-%S-%f'
TestdurationSeconds = 60
# ============================================

reportDF = pd.DataFrame()

# Get the client side FPS, bitqualities, and inter-frame-delays (Note this will be assumed to be "quadrant" delays if running in the partition)
for clientSideLidarFile in clientSideLidarFiles:
    clientSideLidarDF = pd.read_csv(clientSideLidarFile)
    clientSideLidarDF['Timestamp-Obj'] = pd.to_datetime(clientSideLidarDF['Recv-Timestamp'],
                                                             format=DateFormat)

    # Per frame data
    frameStartTimes = []
    frameEndTimes = []
    frameLengths = []
    framePoints = []

    # Process into frames
    currentFrameLengths = 0
    currentFrameTimestamps = []
    currentFramePoints = 0
    lastObservedAzimuth = -1

    for rowIDX, row in clientSideLidarDF.iterrows():
        if row['azimuth'] >= lastObservedAzimuth:
            lastObservedAzimuth = row['azimuth']
            currentFramePoints += 1
            currentFrameLengths += int(row['Length (bytes)'])
            currentFrameTimestamps.append(row['Timestamp-Obj'])

        else:
            # new frame
            frameStartTimes.append(currentFrameTimestamps[0])
            frameEndTimes.append(currentFrameTimestamps[-1])
            frameLengths.append(currentFrameLengths)
            framePoints.append(currentFramePoints)

            # Reset
            lastObservedAzimuth = row['azimuth']
            currentFrameTimestamps = []
            currentFramePoints = 0
            currentFrameLengths = 0

            currentFramePoints += 1
            currentFrameLengths += int(row['Length (bytes)'])
            currentFrameTimestamps.append(row['Timestamp-Obj'])

    interFrameStartTimeDelays = []
    interFrameEndTimeDelays = []

    for timeIndex, timestamp in enumerate(frameStartTimes):
        if timeIndex+1 < len(frameStartTimes):
            nextTimeStamp = frameStartTimes[timeIndex+1]
            interFrameStartTimeDelays.append((nextTimeStamp - timestamp).microseconds)

    for timeIndex, timestamp in enumerate(frameEndTimes):
        if timeIndex+1 < len(frameEndTimes):
            nextTimeStamp = frameEndTimes[timeIndex+1]
            interFrameEndTimeDelays.append((nextTimeStamp - timestamp).microseconds)


    GroupReportRow = pd.DataFrame()

    GroupReportRow['Group-Quadrant'] = [clientSideLidarFile]
    GroupReportRow['Inter-Frame-Avg-Delay-Using-Frame-Start(microseconds)'] = [np.mean(interFrameStartTimeDelays)]
    GroupReportRow['Inter-Frame-STD-Delay-Using-Frame-Start(microseconds)'] = [np.std(interFrameStartTimeDelays)]
    GroupReportRow['Inter-Frame-Avg-Delay-Using-Frame-End(microseconds)'] = [np.mean(interFrameEndTimeDelays)]
    GroupReportRow['Inter-Frame-STD-Delay-Using-Frame-End(microseconds)'] = [np.std(interFrameEndTimeDelays)]
    GroupReportRow['FPS'] = [(len(frameLengths)-2)/TestdurationSeconds]
    GroupReportRow['Bitrate(mbps)'] = [((np.sum(frameLengths) * 8 /1000000)/TestdurationSeconds)]
    GroupReportRow['Per-Frame-Avg-Quality(bytes)'] = [np.mean(frameLengths)]
    GroupReportRow['Per-Frame-STD-Quality(bytes)'] = [np.std(frameLengths)]
    GroupReportRow['Per-Frame-Avg-Density(points)'] = [np.mean(framePoints)]
    GroupReportRow['Per-Frame-STD-Density(points)'] = [np.std(framePoints)]

    reportDF = pd.concat([reportDF, GroupReportRow], axis=0)

# ==============================================

reportDF.to_csv('./data-analysis/lidar-frame-report.csv', index=False)
