import subprocess
import shutil
import os
import glob
import time
import json
import sys
import datetime
import signal
import psutil
from datetime import timezone
import socket

# =======================================================
profilePath = sys.argv[1]
profileFileName = os.path.basename(profilePath)
profileFP = open(profilePath, 'r')
Profile = json.load(profileFP)
profileFP.close()
StartServer = True
StartWait = 3
# ========================================================================
# Attempt to start the server side first
if StartServer:
    coordinatorSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print('Attempting to start server code at {}:{}'.format(Profile['Target-Server-IP'], 7000))
        #coordinatorSocket.settimeout(40)
        coordinatorSocket.connect((Profile['Target-Server-IP'], 7000))
        #coordinatorSocket.settimeout(None)
        coordinatorSocket.send(profilePath.encode())
        coordinatorSocket.close()
        print('TCP Connection Established to server, waiting for startup {}s'.format(StartWait))

        # Wait for warmup
        time.sleep(StartWait)

    except:
        print('Cannot reach server! Stopping.')
        sys.exit()
        exit()

# =======================================================
# sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
# sysctl net.ipv4.tcp_congestion_control
SystemConfiguring = False
SystemCongestionControl = 'cubic'
currentTimeString = datetime.datetime.now(timezone.utc).strftime('%y-%m-%d-%H-%M-%S-%f')
loggingDirName = '{}/Client-{}-{}/'.format(Profile['Client-Logging-Directory'],currentTimeString, SystemCongestionControl)
os.makedirs(loggingDirName, exist_ok=True)
print('AV-Device Starting {} {}'.format(profileFileName, currentTimeString))
# =======================================================

MonitorProc:subprocess.Popen = None
PingProc:subprocess.Popen = None
TraceRouteProc:subprocess.Popen = None
ClientIperfProc:subprocess.Popen = None
ClientCameraProcs:list = []
ClientLiDARProcs:list = []
ClientSensorProcs:list = []
ClientMiscProcs:list = []

# =========================================================================
# Write out the testing audit

testStart = datetime.datetime.now(timezone.utc)

testingInformation = {}
testingInformation['Profile'] = profileFileName
testingInformation['Test-Start-Timestamp'] = testStart.strftime('%y-%m-%d-%H-%M-%S-%f')
testingInformation['Test-Start-Timestamp-Epoch'] = testStart.timestamp()
testingInformation['Number-Of-Cameras'] = len(Profile['Client-Camera-Commands'])
testingInformation['Number-Of-LiDARs'] = len(Profile['Client-LiDAR-Commands'])
testingInformation['Number-Of-Sensors'] = len(Profile['Client-Sensor-Commands'])
testingInformation['Current-System-Congestion-Control'] = SystemCongestionControl
testingInformation['Server-Start'] = StartServer
testingInformation['Server-Start-Wait'] = StartWait

testInforFP = open('{}{}'.format(loggingDirName, 'Test-Information.json'), 'w')
json.dump(testingInformation, testInforFP)
testInforFP.flush()
testInforFP.close()

# =========================================================================

try:

    if Profile['Client-Monitor-Command'] is not None:
        MonitorProc = subprocess.Popen(Profile['Client-Monitor-Command'].split(' '), universal_newlines=False)

    if Profile['Ping-Command'] is not None:
        PingProc = subprocess.Popen(Profile['Ping-Command'].split(' '), universal_newlines=False)

    if Profile['TraceRoute-Command'] is not None:
        TraceRouteProc = subprocess.Popen(Profile['TraceRoute-Command'].split(' '), universal_newlines=False)

    if Profile['Client-Iperf3-Command'] is not None:
        ClientIperfProc = subprocess.Popen(Profile['Client-Iperf3-Command'].split(' '), universal_newlines=False)

    for command in Profile['Client-Camera-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ClientCameraProcs.append(newProc)

    for command in Profile['Client-LiDAR-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ClientLiDARProcs.append(newProc)

    for command in Profile['Client-Sensor-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ClientSensorProcs.append(newProc)

    for command in Profile['Client-Misc-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ClientMiscProcs.append(newProc)

    if Profile['Test-Duration-Seconds'] is not None:
        # Only wait until test is done
        time.sleep(Profile['Test-Duration-Seconds'])
        print('Experiment Done')
        raise KeyboardInterrupt()
    else:
        while(True):
            # Wait for keyboard interupt
            time.sleep(1)

except KeyboardInterrupt as validInterupt:
    print('AV Device Keyboard stopping')
finally:

    if MonitorProc is not None:
        MonitorProc.kill()
        MonitorProc.terminate()
        MonitorProc.wait()

    if PingProc is not None:
        PingProc.kill()
        PingProc.terminate()
        PingProc.wait()

    if TraceRouteProc is not None:
        TraceRouteProc.kill()
        TraceRouteProc.terminate()
        TraceRouteProc.wait()

    if ClientIperfProc is not None:
        ClientIperfProc.kill()
        ClientIperfProc.terminate()
        ClientIperfProc.wait()

    # Kill each subproc
    for cameraProc in ClientCameraProcs:
        try:
            cameraChildren = psutil.Process(cameraProc.pid).children(recursive=True)
            for cameraChild in cameraChildren:
                cameraChild.kill()
            cameraProc.kill()
            cameraProc.terminate()
        except:
            pass

    combinedProcs = []
    combinedProcs.extend(ClientLiDARProcs)
    combinedProcs.extend(ClientSensorProcs)
    combinedProcs.extend(ClientMiscProcs)

    for proc in combinedProcs:
        try:
            procChildren = psutil.Process(proc.pid).children(recursive=True)
            for child in procChildren:
                child.kill()
            proc.terminate()
            proc.kill()
        except Exception as ex:
            print('Proc Cleanup {}'.format(ex))

    print('Log Management ...')

    for logFileName in Profile['Client-File-Cleanups'].keys():
        newFilePath = Profile['Client-File-Cleanups'][logFileName]

        logFiles = glob.glob('./' + logFileName)

        if len(logFiles) > 0:

            for logFile in logFiles:

                if newFilePath is None:
                    # just move to root dir of the logging DIR
                    shutil.move(logFile, loggingDirName + logFile)
                else:
                    # make new dirs ontop of logging dir
                    os.makedirs(loggingDirName + newFilePath, exist_ok=True)
                    shutil.move(logFile, loggingDirName + newFilePath + logFile)

    print('Done')
