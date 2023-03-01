import subprocess
import shutil
import os
import glob
import time
import datetime
from datetime import timezone
import signal
import sys
import json
import psutil

# =============================================================
profilePath = sys.argv[1]
profileFileName = os.path.basename(profilePath)
profileFP = open(profilePath, 'r')
Profile = json.load(profileFP)
profileFP.close()
# =============================================================
checkCCProc = subprocess.Popen('sysctl net.ipv4.tcp_congestion_control'.split(' '), stdout=subprocess.PIPE)
checkCCProc.wait()
ccRawText = checkCCProc.stdout.read()
currentCC = ccRawText.decode().replace('\n','').split(' ')[-1]

currentTimeString = datetime.datetime.now(timezone.utc).strftime('%y-%m-%d-%H-%M-%S-%f')
loggingDirName = '{}Server-{}-{}/'.format(Profile['Server-Logging-Directory'], currentTimeString, currentCC)
os.makedirs(loggingDirName, exist_ok=True)
print('Server for Client Starting {} {}'.format(profileFileName, currentTimeString))
# ============================================================

MonitorProc:subprocess.Popen = None
ServerIperfProc:subprocess.Popen = None
ServerCameraProcs:list = []
ServerLiDARProcs:list = []
ServerSensorProcs:list = []
ServerMiscProcs:list = []

# =========================================================================
# Write out the testing audit

testStart = datetime.datetime.now(timezone.utc)

testingInformation = {}
testingInformation['Profile'] = profileFileName
if Profile['Test-Duration-Seconds'] is not None:
    testingInformation['Server-Test-Duration'] = Profile['Test-Duration-Seconds'] + 15
testingInformation['Test-Start-Timestamp'] = testStart.strftime('%y-%m-%d-%H-%M-%S-%f')
testingInformation['Test-Start-Timestamp-Epoch'] = testStart.timestamp()
testingInformation['Number-Of-Cameras'] = len(Profile['Server-Camera-Commands'])
testingInformation['Number-Of-LiDARs'] = len(Profile['Server-LiDAR-Commands'])
testingInformation['Number-Of-Sensors'] = len(Profile['Server-Sensor-Commands'])
testingInformation['Current-System-Congestion-Control'] = currentCC

testInforFP = open('{}{}'.format(loggingDirName, 'Test-Information.json'), 'w')
json.dump(testingInformation, testInforFP)
testInforFP.flush()
testInforFP.close()

# =========================================================================



try:
    if Profile['Server-Monitor-Command'] is not None:
        MonitorProc = subprocess.Popen(Profile['Server-Monitor-Command'].split(' '), universal_newlines=False)

    if Profile['Server-Iperf3-Command'] is not None:
        ServerIperfProc = subprocess.Popen(Profile['Server-Iperf3-Command'].split(' '), universal_newlines=False)

    for command in Profile['Server-Misc-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ServerMiscProcs.append(newProc)

    for command in Profile['Server-Camera-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ServerCameraProcs.append(newProc)

    for command in Profile['Server-LiDAR-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ServerLiDARProcs.append(newProc)

    for command in Profile['Server-Sensor-Commands']:
        newProc = subprocess.Popen(command.split(' '), universal_newlines=False)
        ServerSensorProcs.append(newProc)

    if Profile['Test-Duration-Seconds'] is not None:
        # Only wait until test is done
        time.sleep(Profile['Test-Duration-Seconds'] + 15)
        print('Experiment Done')
        raise KeyboardInterrupt()
    else:
        while (True):
            # Wait for keyboard interupt
            time.sleep(1)

except KeyboardInterrupt as validInterrupt:
    print('Server for Client: Keyboard Interrupt')
finally:

    if MonitorProc is not None:
        MonitorProc.kill()
        MonitorProc.terminate()
        MonitorProc.wait()

    if ServerIperfProc is not None:
        ServerIperfProc.kill()
        ServerIperfProc.terminate()
        ServerIperfProc.wait()

    for cameraProc in ServerCameraProcs:
        try:
            cameraChildren = psutil.Process(cameraProc.pid).children(recursive=True)
            cameraProc.kill()
            cameraProc.terminate()
        except Exception as ex:
            print(ex)
            print('Camera failed to end')

    combinedProcs = []
    combinedProcs.extend(ServerMiscProcs)
    combinedProcs.extend(ServerLiDARProcs)
    combinedProcs.extend(ServerSensorProcs)

    for proc in combinedProcs:
        try:
            procChildren = psutil.Process(proc.pid).children(recursive=True)
            for child in procChildren:
                child.kill()
            proc.terminate()
            proc.kill()
        except Exception as ex:
            print('Proc Cleanup {}'.format(ex))

    print('Log Managing ...')

    for logFileName in Profile['Server-File-Cleanups'].keys():
        newFilePath = Profile['Server-File-Cleanups'][logFileName]

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