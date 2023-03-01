import subprocess
import glob
import sys
import os
import time
import socket
import datetime
import psutil
import signal

# ==============================================================
#
# ==============================================================

startTimeString = datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S-%f')
IngestIP = sys.argv[1]
IngestPort = int(sys.argv[2])
CameraID = int(sys.argv[3])
#ClientProgram = int(sys.argv[4])
# ==============================================================

cameraProc:subprocess.Popen = None
videoFailures = 0
firstConnectionMade = False
Operate = True

try:
    while Operate:
        # Run until top process calls control C
        if cameraProc is None:
            #currentTimeString = datetime.datetime.now().strftime('%y-%m-%d-%H-%M-%S-%f')

#            cameraCommand = ['ffmpeg', '-rtsp_transport', 'udp', '-i', 'rtsp://{}:{}/camera-{}'.format(IngestIP, IngestPort, CameraID), '-fflags', 'nobuffer', '-vcodec', 'copy', 'rtsp-output-{}-cameranumber-{}-failures-{}.mp4'.format(currentTimeString, CameraID, videoFailures)]
            cameraCommand = ['./openRTSP', '-F', 'rtsp-{}-camera-{}-'.format(IngestPort, CameraID), '-V', '-t', '-m', '-b', '{}'.format(140000), 'rtsp://{}:{}/camera-{}'.format(IngestIP, IngestPort, CameraID)]

            cameraProc = subprocess.Popen(cameraCommand)
            print('RTSP Receiving at {}:{}/camera-{}'.format(IngestIP,IngestPort,CameraID))
        else:
            # Check process status
            returnCode = cameraProc.poll()

            if returnCode is not None:
                # It has died/stopped/completed, restart it
                cameraProc.send_signal(signal.SIGINT)
                cameraProc.wait(4)
                cameraProc = None
                if firstConnectionMade:
                    videoFailures += 1
                print('Stream "Failure" {} Restarting...'.format(videoFailures))
            else:
                firstConnectionMade = True

        time.sleep(1)

except Exception as ex:
    Operate = False
except KeyboardInterrupt as validInterupt:
    print('Camera Driver Client {} Keyboard stopping'.format(IngestPort))
    Operate = False
finally:
    print('Ending Camera Client')
    if cameraProc is not None:
        #cameraProc.send_signal(signal.SIGINT)
        cameraProc.send_signal(signal.SIGHUP)
        #cameraProc.terminate()
        #cameraProc.kill()
        cameraProc.wait(4)
