import glob
import pandas as pd
import numpy as np
import shutil
import os
import datetime
import subprocess
from datetime import datetime, timedelta, timezone
from pytimeparse.timeparse import timeparse

# =============================================================
# Go through each test folder and produce some readable files for use
# =============================================================
ClientTestDirs = glob.glob('../../../Datasets/test-dir/client-data/*/')
ServerTestDirs = glob.glob('../../../Datasets/test-dir/server-data/*/')
TmpDirectory = '../../../Datasets/tmp/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
DateTimeFormat2 = '%Y-%m-%d %H:%M:%S.%f'
CameraLabels = ['camera-1','camera-2','camera-3','camera-4']
CompareVideos = ['../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/output-f.mp4',
                 '../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/output-fl.mp4',
                 '../../../Datasets/sensor-inputs/MnCAV/Vehicle-Cameras/output-fr.mp4',
                 '../../../Datasets/sensor-inputs/Infared-Camera/output-ir.mp4']

TestTruncationEndTime = 300
TestTruncationStartTime = 1
FFProbeFrameStartTag = '[FRAME]'
FFProbeFrameEndTag = '[/FRAME]'
FFProbeByteSizeField = 'pkt_size'

ClientTestDirs.sort(reverse=True)
ServerTestDirs.sort(reverse=True)

# ===============================================================
ProccessFFMPEGData = False

# ===============================================================

def GetVideoData(videoPath:str, altParse:bool=False) -> dict:

    try:

        ffprobeProc = subprocess.Popen(['ffprobe', videoPath], stderr=subprocess.PIPE)
        ffprobeProc.wait()
        resultText = ffprobeProc.stderr.readlines()

        if altParse:
            data1 = resultText[-5].decode()
            data2 = resultText[-4].decode()
        else:
            data1 = resultText[-6].decode()
            data2 = resultText[-1].decode()

        print(data1)
        print(data2)

        returnDict = None

        if 'Stream' in data2 and 'N/A\n' not in data2 and 'bitrate' in data1:
            durationComponent = data1.strip().split(',')[0].split(' ')[1]

            returnDict = dict()

            returnDict['VideoDuration'] = timeparse(durationComponent)

            returnDict['Bitrate'] = data1.strip().split(',')[-1].split(' ')[-2]

            returnDict['FPS'] = data2.strip().split(',')[-4].split(' ')[-2]
    except Exception as ex:
        print('{} failed {}'.format(videoPath, ex))
        returnDict = None

    return returnDict

def ResolveWiresharkPortToRTSPStream(traceFile:str, srcPort:str, dstPort:str='8554') -> str:
    """"""
    tsharkProc = subprocess.Popen(
        [" ".join(['tshark', '-r', traceFile, '\"tcp.dstport == {} and tcp.srcport == {} and rtsp.request and rtsp.session\"'
                  .format(dstPort, srcPort)])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    traceRaw = tsharkProc.stdout.readlines()

    try:

        sessionSetup = traceRaw[-1].decode()

        sessionPieces = sessionSetup.split(' ')

        publishURL = sessionPieces[-2]

        cameraName = publishURL.split('/')[-1]
    except Exception as ex:
        print('Error getting RTSP for srcPort {} {}'.format(srcPort, ex))
        cameraName = None

    return cameraName

def GetWiresharkRTSPFirstFrame(traceFile:str, srcPort:str) -> float:
    """"""
    tsharkProc = subprocess.Popen(
        [" ".join(['tshark', '-r', traceFile, '-Y', '\"tcp.srcport == {} and rtsp.channel\"'.format(srcPort), '-T', 'fields', '-E', 'separator=\",\"', '-e', 'frame.time_epoch'])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    traceRaw = tsharkProc.stdout.readlines()

    if len(traceRaw) > 0:
        # Has a frame to read
        firstFrameLine = traceRaw[1].decode()

        firstFrametime = float(firstFrameLine)

        # Correct to UDT
        return firstFrametime + 18000

    return None

def GetRTSPStreamsAndPorts(traceFile:str) -> pd.DataFrame:
    """"""

    # Get the "start of the trace file"
    capInfosProc = subprocess.Popen(
        [" ".join(['capinfos', traceFile, '-a'])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    capInfosProc.wait()
    timestampForStart = capInfosProc.stdout.readlines()[-1].decode().replace('\n','').split('  ')[-1].strip()[:-3]
    timeStartObject = datetime.strptime(timestampForStart, '%Y-%m-%d %H:%M:%S.%f')

    rtspPortsProc = subprocess.Popen(
        [" ".join(['tshark', '-r', traceFile, '-q', '-z', 'rtp,streams'])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    rtspPortsProc.wait()
    rtspPortsRaw = rtspPortsProc.stdout.readlines()

    #headerLine = rtspPortsRaw[1]
    dataLines = rtspPortsRaw[2:-1]

    totalRTSPStreams = pd.DataFrame()

    for rawLine in dataLines:
        rawLinePieces = rawLine.decode().strip().replace('\n','').replace('     ',' ').replace('    ', ' ').replace('   ', ' ').replace('  ', ' ').split(' ')

        startTime = rawLinePieces[0]
        endTime = rawLinePieces[1]
        sourcePort = rawLinePieces[3]
        packets = rawLinePieces[8]
        lostPackets = rawLinePieces[9]
        lossPercent = rawLinePieces[10]
        minDelta = rawLinePieces[11]
        meanDelta = rawLinePieces[12]
        maxDelta = rawLinePieces[13]
        minJitter = rawLinePieces[14]
        meanJitter = rawLinePieces[15]
        maxJitter = rawLinePieces[16]

        cameraURL = ResolveWiresharkPortToRTSPStream(traceFile, sourcePort)

        streamRow = pd.DataFrame()

        streamRow['Camera-Name'] = [cameraURL]
        streamRow['Stream-Port'] = [sourcePort]
        streamRow['start-time'] = [startTime]
        streamRow['end-time'] = [endTime]

        # Add the stream start to get when the actual stream started, and do the CDT correction
        newStartObject = timeStartObject + timedelta(seconds=float(rawLinePieces[0])) + timedelta(hours=5)
        epochTime = newStartObject.timestamp()

        streamRow['start-time-date'] = [newStartObject]
        streamRow['start-time-epoch'] = [epochTime]
        streamRow['Packet-Count'] = [packets]
        streamRow['Packets-Lost'] = [lostPackets]
        streamRow['Packet-Loss'] = [lossPercent]
        streamRow['Min-Delta(ms)'] = [minDelta]
        streamRow['Mean-Delta(ms)'] = [meanDelta]
        streamRow['Max-Delta(ms)'] = [maxDelta]
        streamRow['Min-Jitter(ms)'] = [minJitter]
        streamRow['Mean-Jitter(ms)'] = [meanJitter]
        streamRow['Max-Jitter(ms)'] = [maxJitter]

        totalRTSPStreams = pd.concat([totalRTSPStreams, streamRow])

    return totalRTSPStreams


def GetWiresharkRetransmits(traceFile:str, srcPort:str, cameraName:str, outputDir:str) -> dict:
    #

    tsharkCommand = ['tshark', '-r', traceFile, '-Y', '\"tcp.srcport=={} and tcp.analysis.retransmission\"'.format(srcPort), '-T', 'fields', '-E', 'separator=\",\"', '-e', 'frame.time_epoch', '-e', 'tcp.analysis.initial_rtt', '-e', 'tcp.analysis.ack_rtt', '>', '{}{}-{}-retransmits.csv'.format(outputDir,cameraName, srcPort)]

    tsharkProc = subprocess.Popen(" ".join(tsharkCommand), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    #traceRaw = tsharkProc.stdout.readlines()

    return None

def GetWiresharkRTT_Camera(traceFile:str, srcPort:str, cameraName:str, outputDir:str) -> None:
    """Get retransmitts"""

    tsharkCommand = ['tshark', '-r', traceFile, '-Y', '\"tcp.srcport=={} and tcp.analysis.ack_rtt\"'.format(srcPort), '-T', 'fields', '-E', 'separator=\",\"', '-e', 'frame.time_epoch', '-e', 'tcp.analysis.initial_rtt', '-e', 'tcp.analysis.ack_rtt', '>', '{}{}-{}-rtts.csv'.format(outputDir,cameraName,srcPort)]

    tsharkProc = subprocess.Popen(" ".join(tsharkCommand), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    #traceRaw = tsharkProc.stdout.readlines()

    return


# ===============================================================


for testID, clientTestDir in enumerate(ClientTestDirs):
    serverTestDir = ServerTestDirs[testID]

    # =============================================================
    # If Camera frames and videos available, figure out bitrates per video samples and per-frame timings
    print('{}/{} - Started {} - {}'.format(testID + 1, len(ClientTestDirs), clientTestDir, serverTestDir))

    cameraReportDF = pd.DataFrame()

    if ProccessFFMPEGData:

        for cameraNum, camera in enumerate(CameraLabels):

            cameraVideos = glob.glob(serverTestDir + 'camera-videos/saved_{}_*.ts'.format(camera))
            cameraVideos.sort()

            if len(cameraVideos) > 0:

                cameraVideoMergeDocument = open(serverTestDir + 'merge.txt', 'w')
                cameraVideosDF = pd.DataFrame()

                recordingEpochTimestamps = []
                recordingTimestamps = []
                bitRates = []
                durations = []
                fpses = []

                for cameraVideo in cameraVideos:

                    videoData = GetVideoData(cameraVideo)

                    recordingTimestamp = cameraVideo.replace(serverTestDir, '').split('/')[-1].replace('.ts', '').replace(
                        'saved_{}_'.format(camera), '')

                    timeStampObj = datetime.strptime(recordingTimestamp, '%Y-%m-%d_%H-%M-%S')
                    epochTimeStamp = timeStampObj.timestamp()

                    if videoData is not None:
                        recordingTimestamps.append(recordingTimestamp)
                        recordingEpochTimestamps.append(epochTimeStamp)
                        bitRates.append(videoData['Bitrate'])
                        durations.append(videoData['VideoDuration'])
                        fpses.append(videoData['FPS'])

                        # put into a merge document
                        cameraVideoMergeDocument.write('file \'camera-videos/{}\'\n'.format(cameraVideo.split('/')[-1]))
                        cameraVideoMergeDocument.flush()

                cameraVideosDF['Video-Segment-Timestamp'] = recordingTimestamps
                cameraVideosDF['Video-Segment-Epoch'] = recordingEpochTimestamps
                cameraVideosDF['Video-Segment-Duration (Seconds)'] = durations
                cameraVideosDF['Video-Segment-Bitrates (Kbps)'] = bitRates
                cameraVideosDF['Video-Segment-FPS'] = fpses

                cameraVideosDF.to_csv(serverTestDir + camera + '-recordings.csv', index=False)

                cameraVideoMergeDocument.flush()
                cameraVideoMergeDocument.close()

                # Merge the video recordings into one
                mergedVideoFileName = '{}-merged.mp4'.format(camera)
                if os.path.exists(serverTestDir + mergedVideoFileName):
                    os.remove(serverTestDir + mergedVideoFileName)

                try:

                    mergeProc = subprocess.Popen(
                        ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', serverTestDir + 'merge.txt', '-c', 'copy',
                         serverTestDir + mergedVideoFileName])
                    mergeProc.wait()

                    print('Processing PSNR/SSIM, there will be delay')

                    # Get the PSNR and SSIM values
                    ffmpegPSNRProc = subprocess.Popen(
                        ['ffmpeg', '-i', serverTestDir + mergedVideoFileName, '-i', CompareVideos[cameraNum], '-lavfi',
                         'psnr=stats_file={}{}-psnr.txt'.format(serverTestDir, camera), '-f',
                         'null', '-'], stderr=subprocess.PIPE)
                    ffmpegPSNRProc.wait()
                    psnrresultText = ffmpegPSNRProc.stderr.readlines()
                    psnrResult = psnrresultText[-1].decode()
                    psnrAvg = float(psnrResult.split(' ')[-3].split(':')[-1])

                    psnrFP = open('{}{}-psnr.txt'.format(serverTestDir, camera), 'r')
                    psnrFileLines = psnrFP.readlines()
                    psnrFP.close()

                    allValues = []

                    for line in psnrFileLines:
                        psnrValue = line.split(' ')[-5].split(':')[-1]
                        allValues.append(psnrValue)

                    psnrDF = pd.DataFrame()
                    psnrDF['PSNR'] = allValues
                    psnrDF.to_csv(serverTestDir + camera + '-psnr.csv', index=False)

                    ffmpegSSIMProc = subprocess.Popen(
                        ['ffmpeg', '-i', serverTestDir + mergedVideoFileName, '-i', CompareVideos[cameraNum], '-lavfi',
                         'ssim=stats_file={}{}-ssim.txt'.format(serverTestDir, camera),
                         '-f', 'null', '-'], stderr=subprocess.PIPE)
                    ffmpegSSIMProc.wait()
                    ssimresultText = ffmpegSSIMProc.stderr.readlines()
                    ssimResult = ssimresultText[-1].decode()
                    ssimAvg = float(ssimResult.split(' ')[-2].split(':')[-1])

                    # Generate a per-frame SSIM file
                    ssimFP = open('{}{}-ssim.txt'.format(serverTestDir, camera), 'r')
                    ssimFileLines = ssimFP.readlines()
                    ssimFP.close()

                    allValues = []

                    for line in ssimFileLines:
                        ssimValue = line.split(' ')[-2].split(':')[-1]
                        allValues.append(ssimValue)

                    ssimDF = pd.DataFrame()
                    ssimDF['SSIM'] = allValues
                    ssimDF.to_csv(serverTestDir + camera + '-ssim.csv', index=False)

                    mergedVideoData = GetVideoData(serverTestDir + mergedVideoFileName, True)

                    cameraReportRow = pd.DataFrame()
                    cameraReportRow['Camera'] = [camera]
                    cameraReportRow['Total Duration (seconds)'] = [mergedVideoData['VideoDuration']]
                    cameraReportRow['Avg FPS'] = [mergedVideoData['FPS']]
                    cameraReportRow['Avg Bitrate Kbps'] = [mergedVideoData['Bitrate']]
                    cameraReportRow['Avg PSNR'] = [psnrAvg]
                    cameraReportRow['Avg SSIM'] = [ssimAvg]

                    cameraReportDF = pd.concat([cameraReportDF, cameraReportRow])

                    print('Processing Per-frame bitrates, this will be slow')
                    # Generate a frames over time file
                    perFrameFilePath = serverTestDir + '{}-per-frame.txt'.format(camera)
                    if os.path.exists(perFrameFilePath) is False:
                        ffProbeFrameProc = subprocess.Popen(
                            ' '.join(
                                ['ffprobe', serverTestDir + mergedVideoFileName, '-show_frames', '>', perFrameFilePath]),
                            shell=True)
                        ffProbeFrameProc.wait()

                    # Parse the per-frame into a csv of frame and bitrate
                    perFrameBitRatesFP = open(perFrameFilePath, 'r')
                    perFrameFileLines = perFrameBitRatesFP.readlines()
                    perFrameBitRatesFP.close()

                    frameByteQualities = []

                    for lineIdx, line in enumerate(perFrameFileLines):
                        if FFProbeByteSizeField in line:
                            frameBytes = int(line.split('=')[-1].replace('\n', ''))
                            frameByteQualities.append(frameBytes)

                    frameQualityDF = pd.DataFrame()
                    frameQualityDF['Frame-Bytes'] = frameByteQualities
                    frameQualityDF['Frame-Bits'] = np.multiply(frameByteQualities, 8)

                    frameQualityDF.to_csv(serverTestDir + camera + '-frame-qualities.csv', index=False)

                except Exception as ex1:
                    print('Video error {}'.format(ex1))


    tracefiles = glob.glob(serverTestDir + '*.pcap')

    rtspStreams:pd.DataFrame = None

    if len(tracefiles) > 0:
        rtspStreams = GetRTSPStreamsAndPorts(tracefiles[0])

        for rowIDX, row in rtspStreams.iterrows():
            cameraName = row['Camera-Name']
            cameraPort = row['Stream-Port']

            # Get the specific camera RTTs and Retransmits
            GetWiresharkRTT_Camera(tracefiles[0], cameraPort, cameraName, serverTestDir)
            GetWiresharkRetransmits(tracefiles[0],cameraPort, cameraName, serverTestDir)

        if len(rtspStreams) > 0:
            rtspStreams.to_csv(serverTestDir + 'rtsp-streams.csv', index=False)

    for cameraID, camera in enumerate(CameraLabels):
        cameraFrames = glob.glob(serverTestDir + 'camera-frames/rtsp-*-{}-video-*'.format(camera))

        if len(cameraFrames) > 0:

            if rtspStreams is not None:
                specificCameraStreamDF = rtspStreams[rtspStreams['Camera-Name'] == camera]
                specificCameraStreamDF = specificCameraStreamDF.sort_values(by='start-time-epoch')
                startTimeEpoch = specificCameraStreamDF.iloc[0]['start-time-epoch']
                # Now take this value and use it as the "frame-time-since-stream-start" metric

                cameraFramesDF = pd.DataFrame()

                cameraFrames.sort()

                frameTimestamps = []
                frameDateTimestamps = []
                frameSizes = []
                frameTimeFromStreamStart = []
                firstFrameDelay = None


                for cameraFrame in cameraFrames:
                    # Parse out the timestamp of the RTP frame
                    frameSize = os.path.getsize(cameraFrame)
                    frameSizes.append(frameSize)
                    epochTime = cameraFrame.replace(serverTestDir, '').split('/')[-1].split('-')[7]
                    timeStamp = float(epochTime)
                    dateTimeData = datetime.fromtimestamp(timeStamp)
                    # Convert from CDT to UDT
                    dateTimeData = dateTimeData + timedelta(hours=5)
                    dateTimeStamp = dateTimeData.strftime('%y-%m-%d-%H-%M-%S-%f')

                    if firstFrameDelay is None:
                        firstFrameDelay = dateTimeData.timestamp() - startTimeEpoch

                    frameTimestamps.append(dateTimeData.timestamp())
                    frameDateTimestamps.append(dateTimeStamp)


                cameraFramesDF['Frame-Epoch-Timestamp'] = frameTimestamps
                cameraFramesDF['Inter-Frame-Times (s)'] = cameraFramesDF['Frame-Epoch-Timestamp'].diff()
                cameraFramesDF['Frame-Timestamp'] = frameDateTimestamps
                cameraFramesDF['Frame-Sizes (Bytes)'] = frameSizes
                cameraFramesDF['Frame-Sizes (Bits)'] = np.multiply(frameSizes, 8)
                cameraFramesDF['Frame-Time-With-First-Frame-Delay(s)'] = cameraFramesDF['Inter-Frame-Times (s)'] + firstFrameDelay

                cameraFramesDF.to_csv(serverTestDir + camera + '-frames.csv', index=False)

    if len(cameraReportDF) >= 1:
        cameraReportDF.to_csv(serverTestDir + 'cameras-quality.csv', index=False)


