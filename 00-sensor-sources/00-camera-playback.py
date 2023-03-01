import subprocess
import glob
import sys
import os
import time
import socket
from datetime import datetime, timedelta, timezone
import json

# ===================================================

TargetIP = sys.argv[1]
TargetPort = int(sys.argv[2])
IngestVideoFile = sys.argv[3]
EncodingApproach = sys.argv[4]
EncodingScheme = int(sys.argv[5])
RTSPTransport = sys.argv[6]
CameraNumber = sys.argv[7]
LogFileFP = open('./camera-{}-audit-log.csv'.format(CameraNumber),'w')
LogFileFP.write('Timestamp,Timestamp-Epoch,Event-Type\n')
LogFileFP.flush()

# ---------------------------
# General Args
HideOutput = True
# ---------------------------
# Constant Rate Factor Args (CRF)
CRFValue = 23

# ---------------------------
# Constant Bitrate Args (CBR)
InputResolution = 'scale=1024:768'
OutputFrameRate = '30'
CameraTargetBitRateAvgKb = 4456

# ===================================================
EncodingSchemes = ['CRF','CBR','VBR','Capped-CRF']

cameraCommand = None

if EncodingScheme == 0:
    print('Attempting to {} with {}'.format(RTSPTransport, TargetPort))
    # CRF
    cameraCommand = ['ffmpeg', '-hide_banner', '-re', '-i', IngestVideoFile,
                     '-vcodec', EncodingApproach, '-crf', '{}'.format(CRFValue), '-f', 'rtsp', '-rtsp_transport', RTSPTransport,
                 'rtsp://{}:{}/camera-{}'.format(TargetIP, TargetPort, CameraNumber)]


elif EncodingScheme == 1:
    # CBR command
    cameraCommand = ['ffmpeg', '-hide_banner', '-re', '-i',
                     IngestVideoFile, '-vcodec', EncodingApproach,
                     '-map', '0:v', '-fflags', 'nobuffer', '-vf', InputResolution,
                     '-r', OutputFrameRate, '-b:v', '{}K'.format(CameraTargetBitRateAvgKb),
                     '-maxrate', '{}K'.format(int(CameraTargetBitRateAvgKb*1.50)),
                     '-minrate', '{}K'.format(int(CameraTargetBitRateAvgKb/2)),
                     '-bufsize', '{}K'.format(int(CameraTargetBitRateAvgKb*1.50)),
                     '-f', 'rtsp', '-rtsp_transport', RTSPTransport,
                     'rtsp://{}:{}/camera-{}'.format(TargetIP, TargetPort, CameraNumber), '-']


cameraProc:subprocess.Popen = None
videoFailures = 0
firstConnectionMade = False
Operate = True

if cameraCommand is not None:

    try:
        while Operate:
            # Run until top process calls control C
            if cameraProc is None:
                #currentTimeString = datetime.now().strftime('%y-%m-%d-%H-%M-%S-%f')
                # Start first time
                # stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                camerastartTime = datetime.now(timezone.utc)
                LogFileFP.write('{},{},{}\n'.format(camerastartTime.strftime('%y-%m-%d-%H-%M-%S-%f'),camerastartTime.timestamp(), 'CAMERA-PRE-START'))
                LogFileFP.flush()
                if HideOutput:
                    cameraProc = subprocess.Popen(cameraCommand, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=False)
                else:
                    cameraProc = subprocess.Popen(cameraCommand, universal_newlines=False)
                camerastartTime = datetime.now(timezone.utc)
                LogFileFP.write('{},{},{}\n'.format(camerastartTime.strftime('%y-%m-%d-%H-%M-%S-%f'),camerastartTime.timestamp(), 'CAMERA-START'))
                LogFileFP.flush()
                print('RTSP Streaming to {} {}:{}/camera-{} - {}'.format(RTSPTransport, TargetIP,TargetPort, CameraNumber, EncodingSchemes[EncodingScheme]))
            else:
                # Check process status
                returnCode = cameraProc.poll()

                if returnCode is not None:
                    # It has died/stopped/completed, restart it
                    cameraProc.terminate()
                    cameraProc.kill()
                    cameraProc.wait()
                    cameraProc = None
                    if firstConnectionMade:
                        videoFailures += 1
                        cameraEventTime = datetime.now(timezone.utc)
                        LogFileFP.write('{},{},{}\n'.format(cameraEventTime.strftime('%y-%m-%d-%H-%M-%S-%f'),cameraEventTime.timestamp(), 'CAMERA-FAILURE-TO-CONNECT'))
                        LogFileFP.flush()
                    else:
                        cameraEventTime = datetime.now(timezone.utc)
                        LogFileFP.write('{},{},{}\n'.format(cameraEventTime.strftime('%y-%m-%d-%H-%M-%S-%f'),cameraEventTime.timestamp(), 'CAMERA-ATTEMPT'))
                        LogFileFP.flush()
                    print('Stream "Failure" Restarting...')
                else:
                    if not firstConnectionMade:
                        firstConnectionMade = True
                        cameraEventTime = datetime.now(timezone.utc)
                        LogFileFP.write('{},{},{}\n'.format(cameraEventTime.strftime('%y-%m-%d-%H-%M-%S-%f'),cameraEventTime.timestamp(), 'FIRST-CONNECTION-MADE'))
                        LogFileFP.flush()

            time.sleep(1)

    except KeyboardInterrupt as validInterupt:
        print('Camera {} Keyboard Stopping'.format(TargetPort))
        Operate = False
    finally:
        print('Camera Ending')
        cameraEventTime = datetime.now(timezone.utc)
        LogFileFP.write('{},{},{}\n'.format(cameraEventTime.strftime('%y-%m-%d-%H-%M-%S-%f'),cameraEventTime.timestamp(), 'CAMERA-END'))
        LogFileFP.flush()

        if cameraProc is not None:
            cameraProc.terminate()
            cameraProc.kill()
            cameraProc.wait()

        LogFileFP.flush()
        LogFileFP.close()

else:
    print('Error: Camera Command is None (Eg: Invalid)')
