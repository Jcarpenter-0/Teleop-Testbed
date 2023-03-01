import glob
import pandas as pd
import numpy as np
import shutil
import os
import datetime
import subprocess
from datetime import datetime, timedelta, timezone
from pytimeparse.timeparse import timeparse
import zlib

# =============================================================
# Go through each test folder and produce some readable files for use
# =============================================================
ClientTestDirs = glob.glob('../../../Datasets/client-data/*/output/*/')
ServerTestDirs = glob.glob('../../../Datasets/server-data/*/output/*/')
TmpDirectory = '../../../Datasets/tmp/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
DateTimeFormat2 = '%Y-%m-%d %H:%M:%S.%f'
CameraLabels = ['camera-1','camera-2','camera-3','camera-4']
SensorSendPorts = ['2379','2380','2381','8319','8320','8321','4000','4001','4002','4003','4004','4005']
CompareVideos = ['../00-sensor-sources/MnCAV/Vehicle-Cameras/output-f.mp4',
                 '../00-sensor-sources/MnCAV/Vehicle-Cameras/output-fl.mp4',
                 '../00-sensor-sources/MnCAV/Vehicle-Cameras/output-fr.mp4',
                 '../00-sensor-sources/Infared-Camera/output-ir.mp4']

TestTruncationEndTime = 300
TestTruncationStartTime = 1
FFProbeFrameStartTag = '[FRAME]'
FFProbeFrameEndTag = '[/FRAME]'
FFProbeByteSizeField = 'pkt_size'

# =============================================================
# Debugging Flags
ProcessCameras = False
ProcessRawVideos = False
ProcessWireshark = False
ProcessTransmittedData = False
ProcessServerSideTputs = False
MakeSegmentFilesFromTransmittedData = False

# =============================================================
ClientTestDirs.sort(reverse=True)
ServerTestDirs.sort(reverse=True)
# =============================================================

def ProcessMFRGPSText(row) -> dict:

    # example Location|LATITUDE|44.97609|LONGITUDE|-93.26087|ALTITUDE|248 m|SATELLITES|8|+|−
    pieces = row['Location-Text'].split('|')
    data = dict()

    data['Latitude'] = pieces[2]
    data['Longitude'] = pieces[4]
    data['Altitude'] = pieces[6]
    data['Satellites'] = pieces[8]

    return data

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

def ProcessWiresharkBytes(traceFile:str, filterString:str='BYTES()udp', timeStart:int=12, timeLimit:int=299) -> dict:
    tsharkProc = subprocess.Popen(
        [" ".join(['tshark', '-r', traceFile, '-q', '-z', 'io,stat,1,\"{}\"'.format(filterString)])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    traceRaw = tsharkProc.stdout.readlines()

    tputs = []

    for rawRow in traceRaw[timeStart + 11:timeLimit]:
        pieces = rawRow.decode().split('|')

        byteAmount = int(pieces[2].strip())

        tputs.append(byteAmount)

    # Get timestamps
    capInfosProc = subprocess.Popen(
        [" ".join(['capinfos', traceFile, '-a'])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    capInfosProc.wait()
    timestampForStart = capInfosProc.stdout.readlines()[-1].decode().replace('\n','').split('  ')[-1].strip()[:-3]
    timeStartObject = datetime.strptime(timestampForStart, '%Y-%m-%d %H:%M:%S.%f')

    #capInfosProc = subprocess.Popen(
    #    [" ".join(['capinfos', traceFile, '-a', '-S'])], stdout=subprocess.PIPE,
    #    stderr=subprocess.PIPE, shell=True)
    #capInfosProc.wait()
    #timestamptEpochForStart = float(capInfosProc.stdout.readlines()[-1].decode().replace('\n','').split(' ')[-1])

    times = []
    timesEpochs = []

    adjustedTimeStartObject = timeStartObject + timedelta(hours=5)

    for secondTimestep in range(len(tputs)):
        timeAdd = adjustedTimeStartObject.timestamp() + secondTimestep
        timesEpochs.append(timeAdd)
        newTimeObject = adjustedTimeStartObject + timedelta(seconds=secondTimestep)
        times.append(newTimeObject.strftime(DateTimeFormat))

    return {"tputs":tputs,"times":times,"times-epochs":timesEpochs}

def ResolveWiresharkPortToRTSPStream(traceFile:str, srcPort:str, dstPort:str='8554') -> str:
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

def GetWiresharkRTT(traceFile:str, srcPort:str) -> dict:
    #

    tsharkCommand = ['tshark', '-r', traceFile, '-Y', '\"tcp.srcport=={} and tcp.analysis.ack_rtt\"'.format(srcPort), '-T', 'fields', '-e', 'frame.time', '-e', 'tcp.analysis.ack_rtt']

    tsharkProc = subprocess.Popen(" ".join(tsharkCommand), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    traceRaw = tsharkProc.stdout.readlines()

    # Return the Initial-RTT,

    rttData = dict()

    rttData['']

    return rttData


# =============================================================
for testID, clientTestDir in enumerate(ClientTestDirs):
    serverTestDir = ServerTestDirs[testID]

    # =============================================================
    # If Camera frames and videos available, figure out bitrates per video samples and per-frame timings
    print('{}/{} - Started'.format(testID + 1, len(ClientTestDirs)))

    if ProcessCameras:

        # Process the bitrates and SSIM and PSNR for recorded videos

        cameraReportDF = pd.DataFrame()

        if ProcessRawVideos:
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


                        mergeProc = subprocess.Popen(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', serverTestDir + 'merge.txt', '-c', 'copy', serverTestDir + mergedVideoFileName])
                        mergeProc.wait()

                        print('Processing PSNR/SSIM, there will be delay')

                        # Get the PSNR and SSIM values
                        ffmpegPSNRProc = subprocess.Popen(
                            ['ffmpeg', '-i', serverTestDir + mergedVideoFileName, '-i', CompareVideos[cameraNum], '-lavfi', 'psnr=stats_file={}{}-psnr.txt'.format(serverTestDir,camera), '-f',
                             'null', '-'], stderr=subprocess.PIPE)
                        ffmpegPSNRProc.wait()
                        psnrresultText = ffmpegPSNRProc.stderr.readlines()
                        psnrResult = psnrresultText[-1].decode()
                        psnrAvg = float(psnrResult.split(' ')[-3].split(':')[-1])

                        psnrFP = open('{}{}-psnr.txt'.format(serverTestDir,camera),'r')
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
                            ['ffmpeg', '-i', serverTestDir + mergedVideoFileName, '-i', CompareVideos[cameraNum], '-lavfi', 'ssim=stats_file={}{}-ssim.txt'.format(serverTestDir,camera),
                             '-f', 'null', '-'], stderr=subprocess.PIPE)
                        ffmpegSSIMProc.wait()
                        ssimresultText = ffmpegSSIMProc.stderr.readlines()
                        ssimResult = ssimresultText[-1].decode()
                        ssimAvg = float(ssimResult.split(' ')[-2].split(':')[-1])

                        # Generate a per-frame SSIM file
                        ssimFP = open('{}{}-ssim.txt'.format(serverTestDir,camera),'r')
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
                                ' '.join(['ffprobe', serverTestDir + mergedVideoFileName, '-show_frames', '>', perFrameFilePath]), shell=True)
                            ffProbeFrameProc.wait()

                        # Parse the per-frame into a csv of frame and bitrate
                        perFrameBitRatesFP = open(perFrameFilePath, 'r')
                        perFrameFileLines = perFrameBitRatesFP.readlines()
                        perFrameBitRatesFP.close()

                        frameByteQualities = []

                        for lineIdx, line in enumerate(perFrameFileLines):
                            if FFProbeByteSizeField in line:
                                frameBytes = int(line.split('=')[-1].replace('\n',''))
                                frameByteQualities.append(frameBytes)

                        frameQualityDF = pd.DataFrame()
                        frameQualityDF['Frame-Bytes'] = frameByteQualities
                        frameQualityDF['Frame-Bits'] = np.multiply(frameByteQualities, 8)

                        frameQualityDF.to_csv(serverTestDir + camera + '-frame-qualities.csv', index=False)

                    except Exception as ex1:
                        print('Video error {}'.format(ex1))

        for camera in CameraLabels:
            cameraFrames = glob.glob(serverTestDir + 'camera-frames/rtsp-*-{}-video-*'.format(camera))

            if len(cameraFrames) > 0:
                cameraFramesDF = pd.DataFrame()

                cameraFrames.sort()

                frameTimestamps = []
                frameDateTimestamps = []
                frameSizes = []

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
                    frameTimestamps.append(dateTimeData.timestamp())
                    frameDateTimestamps.append(dateTimeStamp)

                cameraFramesDF['Frame-Epoch-Timestamp'] = frameTimestamps
                cameraFramesDF['Inter-Frame-Times (s)'] = cameraFramesDF['Frame-Epoch-Timestamp'].diff()
                cameraFramesDF['Frame-Timestamp'] = frameDateTimestamps
                cameraFramesDF['Frame-Sizes (Bytes)'] = frameSizes
                cameraFramesDF['Frame-Sizes (Bits)'] = np.multiply(frameSizes, 8)
                #try:
                #    cameraPSNRDF = pd.read_csv(serverTestDir + '{}-psnr.csv'.format(camera))
                #    cameraSSIMDF = pd.read_csv(serverTestDir + '{}-ssim.csv'.format(camera))

                #    cameraFramesDF = pd.concat([cameraFramesDF, cameraSSIMDF], axis=1, ignore_index=True)
                #    cameraFramesDF = pd.concat([cameraFramesDF, cameraPSNRDF], axis=1, ignore_index=True)
                #except:
                #    print('{} issue locating the PSNR/SSIM'.format(camera))

                cameraFramesDF.to_csv(serverTestDir + camera + '-frames.csv', index=False)

        if len(cameraReportDF) >= 1:
            cameraReportDF.to_csv(serverTestDir + 'cameras-quality.csv', index=False)

        print('{}/{} - Cameras Done'.format(testID+1, len(ClientTestDirs)))

    if ProcessServerSideTputs:
        sensorLogs = glob.glob(serverTestDir + 'sensor--*-audit-logs.csv')

        for sensorLog in sensorLogs:
            sensorPort = sensorLog.split('/')[-1].split('-')[2]

            sensorLogDF = pd.read_csv(sensorLog)

            epochTimes = []

            for rowIDX, row in sensorLogDF.iterrows():

                dateFormat = row['Receive-Timestamp']

                if '+' in dateFormat:
                    dateFormat = row['Receive-Timestamp'][:-6]

                if '.' not in dateFormat:
                    dateFormat = '{}.000000'.format(dateFormat)

                #print(dateFormat)

                timePriorToConversion = datetime.strptime(dateFormat, DateTimeFormat2)
                epochTimes.append(timePriorToConversion.timestamp())

            tputsAltDF = pd.DataFrame()

            tputsAltDF['Receive-Timestamp'] = sensorLogDF['Receive-Timestamp']
            tputsAltDF['Receive-Epochs'] = epochTimes
            tputsAltDF['{}-tputs'.format(sensorPort)] = np.multiply(sensorLogDF['Length-Of-Chunk-Received(Bytes)'], 8)

            tputsAltDF.to_csv(serverTestDir + '{}-processed-tputs.csv'.format(sensorPort), index=False)


    print('Starting WireShark Parses ~ this will be long')

    if ProcessWireshark:

        tracefiles = glob.glob(clientTestDir + '*.pcapng')

        if len(tracefiles) > 0:

            udpData = ProcessWiresharkBytes(tracefiles[0], 'BYTES()udp', timeStart=TestTruncationStartTime, timeLimit=TestTruncationEndTime)
            tcpData = ProcessWiresharkBytes(tracefiles[0], 'BYTES()tcp', timeStart=TestTruncationStartTime, timeLimit=TestTruncationEndTime)
            nonData = ProcessWiresharkBytes(tracefiles[0], 'BYTES()not udp and not tcp', timeStart=TestTruncationStartTime, timeLimit=TestTruncationEndTime)

            tputsDF = pd.DataFrame()
            tputsDF['Timestamp'] = udpData['times']
            tputsDF['Timestamp-Epoch'] = udpData['times-epochs']
            tputsDF['UDP-Bytes'] = udpData['tputs']
            tputsDF['TCP-Bytes'] = tcpData['tputs']
            tputsDF['Nons-Bytes'] = nonData['tputs']
            tputsDF['UDP-Bits'] = np.multiply(udpData['tputs'], 8)
            tputsDF['TCP-Bits'] = np.multiply(tcpData['tputs'], 8)
            tputsDF['Nons-Bits'] = np.multiply(nonData['tputs'], 8)

            # Get the ports RTSP used for communicating the actual stream data
            rtspPortsToCameras = dict()

            rtspPortsProc = subprocess.Popen(
                [" ".join(['tshark', '-r', tracefiles[0], '-q', '-z', 'rtp,streams'])], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, shell=True)
            rtspPortsProc.wait()
            rtspPortsRaw = rtspPortsProc.stdout.readlines()

            for rawLine in rtspPortsRaw[2:-1]:
                rawLinePieces = rawLine.decode().replace('    ', '   ').split(' ')

                sourcePort = rawLinePieces[11]

                cameraURL = ResolveWiresharkPortToRTSPStream(tracefiles[0], sourcePort)

                if cameraURL is not None:
                    rtspPortsToCameras[sourcePort] = cameraURL

            for appPort in rtspPortsToCameras.keys():

                specificPortUDPTputs = ProcessWiresharkBytes(tracefiles[0], 'BYTES()udp.srcport == {}'.format(appPort), timeStart=TestTruncationStartTime, timeLimit=TestTruncationEndTime)
                specificPortTCPTputs = ProcessWiresharkBytes(tracefiles[0], 'BYTES()tcp.srcport == {}'.format(appPort), timeStart=TestTruncationStartTime, timeLimit=TestTruncationEndTime)

                appName = appPort

                if appPort in rtspPortsToCameras.keys():
                    appName = '{}'.format(rtspPortsToCameras[appPort])

                tputsDF['UDP-{}-Bytes'.format(appName)] = specificPortUDPTputs['tputs']
                tputsDF['TCP-{}-Bytes'.format(appName)] = specificPortTCPTputs['tputs']
                tputsDF['UDP-{}-Bits'.format(appName)] = np.multiply(specificPortUDPTputs['tputs'], 8)
                tputsDF['TCP-{}-Bits'.format(appName)] = np.multiply(specificPortTCPTputs['tputs'], 8)

            for appPort in SensorSendPorts:

                specificPortUDPTputs = ProcessWiresharkBytes(tracefiles[0], 'BYTES()udp.dstport == {}'.format(appPort),
                                                             timeStart=TestTruncationStartTime, timeLimit=TestTruncationEndTime)
                specificPortTCPTputs = ProcessWiresharkBytes(tracefiles[0], 'BYTES()tcp.dstport == {}'.format(appPort),
                                                             timeStart=TestTruncationStartTime, timeLimit=TestTruncationEndTime)

                appName = appPort

                if appPort in rtspPortsToCameras.keys():
                    appName = '{}'.format(rtspPortsToCameras[appPort])

                tputsDF['UDP-{}-Bytes'.format(appName)] = specificPortUDPTputs['tputs']
                tputsDF['TCP-{}-Bytes'.format(appName)] = specificPortTCPTputs['tputs']
                tputsDF['UDP-{}-Bits'.format(appName)] = np.multiply(specificPortUDPTputs['tputs'], 8)
                tputsDF['TCP-{}-Bits'.format(appName)] = np.multiply(specificPortTCPTputs['tputs'], 8)

            tputsDF.to_csv(clientTestDir + 'throughputs.csv', index=False)
        else:
            print('{} has no wireshark!'.format(clientTestDir))

        print('{}/{} - Wiresharks Done'.format(testID+1, len(ClientTestDirs)))

    if ProcessTransmittedData:

        print('Doing server-side post-processing of received data')
        for sensorPort in SensorSendPorts:

            sentDataFiles = glob.glob(serverTestDir + 'sensor--{}-tagged-*.data'.format(sensorPort))

            if len(sentDataFiles) <= 0:
                sentDataFiles = glob.glob(serverTestDir + 'sensor-{}-tagged-*.data'.format(sensorPort))

            serverSideAuditLogs = glob.glob(serverTestDir + 'sensor--{}-audit-logs.csv'.format(sensorPort))

            # Clean up the tmp files for reuse of the directory
            tmpFiles = glob.glob(TmpDirectory + '*')

            for tmpFile in tmpFiles:
                os.remove(tmpFile)

            if len(serverSideAuditLogs) > 0 and len(sentDataFiles) > 0:

                sensorAuditLogDF = pd.read_csv(serverSideAuditLogs[0])
                sensorDataFP = open(sentDataFiles[0], 'rb')

                dataLogFileFP = open(serverTestDir + '{}-post-process-logs.csv'.format(sensorPort),'w')
                dataLogFileFP.write('ObservationID,PartID,Receive-Timestamp,Epoch-Receive-Timestamp,Length-Of-Chunk-Received(Bytes),Tag-Length(Bytes)\n')
                dataLogFileFP.flush()

                for rowIDX, row in sensorAuditLogDF.iterrows():
                    readAmount = row['Length-Of-Chunk-Received(Bytes)']

                    dataChunk = sensorDataFP.read(readAmount)

                    # Extract the interior tag, last n bytes (defined by the sender side tag length)
                    taggingOffset = 0
                    continueUnpacking = True
                    while continueUnpacking:
                        tagStartIndex = dataChunk.find(b'#!#')
                        tagMiddleIndex = dataChunk.find(b'#!#', tagStartIndex + 1)
                        tagEndIndex = dataChunk.find(b'#!#', tagMiddleIndex + 1)
                        tagBytes = dataChunk[tagStartIndex:tagEndIndex+3]

                        taggingOffset += tagEndIndex + 3

                        partIDComponent = dataChunk[tagStartIndex + 3:tagMiddleIndex]
                        obvIDComponent = dataChunk[tagMiddleIndex + 3:tagEndIndex]

                        partID = int.from_bytes(partIDComponent, 'big')
                        observationID = int.from_bytes(obvIDComponent, 'big')

                        #print('Part {} Obv {}'.format(partID, observationID))

                        dataChunk = dataChunk[:tagStartIndex]

                        # Write each datachunk out for later conncatonation
                        if MakeSegmentFilesFromTransmittedData:
                            dataChunkFP = open(TmpDirectory + '{}-{}.segment'.format(observationID, partID), 'wb')
                            dataChunkFP.write(dataChunk)
                            dataChunkFP.flush()
                            dataChunkFP.close()

                        recvTag = sensorDataFP.read(row['Tag-Length(Bytes)'])
                        recvDateRaw = recvTag.decode().replace('#!#', '')
                        epochTime = datetime.strptime(recvDateRaw,DateTimeFormat).timestamp()

                        dataLogFileFP.write('{},{},{},{},{},{}\n'.format(observationID, partID, recvDateRaw, epochTime,len(dataChunk), len(tagBytes)))
                        dataLogFileFP.flush()

                        # If there is no more tags to unpack, then we must end
                        continueUnpacking = dataChunk.count(b'#!#', taggingOffset) >= 3

                dataLogFileFP.close()
                sensorDataFP.close()

                if MakeSegmentFilesFromTransmittedData:
                    # Reassemble files (from the tmp) into a single observation files (which will need to be decompressed at that level)
                    postProcessLogDF = pd.read_csv(serverTestDir + '{}-post-process-logs.csv'.format(sensorPort))

                    if len(postProcessLogDF) > 0:
                        try:
                            os.mkdir(serverTestDir + '{}-obvs'.format(sensorPort))
                        except:
                            print('Obvs folder exists already, continuing')

                    observations = postProcessLogDF['ObservationID'].unique()

                    for observation in observations:

                        segmentFiles = glob.glob(TmpDirectory + '{}-*.segment'.format(observation))
                        segmentFiles.sort()

                        if len(segmentFiles) > 0:
                            observationFP = open(serverTestDir + '{}-obvs/'.format(sensorPort) + '{}.obv'.format(observation), 'wb')

                            for segmentFile in segmentFiles:
                                print('Combining Segment {}'.format(segmentFile))
                                segmentFileFP = open(segmentFile,'rb')

                                segmentData = segmentFileFP.read()

                                segmentFileFP.close()

                                observationFP.write(segmentData)
                                observationFP.flush()

                            observationFP.flush()
                            observationFP.close()
