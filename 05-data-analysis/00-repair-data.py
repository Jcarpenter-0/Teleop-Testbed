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
# Go through each test folder and clean up data if need be
# =============================================================
ClientTestDirs = glob.glob('../../../Datasets/client-data/*/output/*/')
ServerTestDirs = glob.glob('../../../Datasets/server-data/*/output/*/')

CorrectObvName = True
CorrectCDT = False
CorrectCDT_Tputs = False

# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
SensorSendPorts = ['2379','2380','2381','8319','8320','8321','4000','4001','4002','4003','4004','4005']
ClientTestDirs.sort(reverse=True)
ServerTestDirs.sort(reverse=True)

# ==============================================================
# Convert timestamps of various logs to UDT with same format (and include the epoch time)

# throughputs.csv
# xr90-mobile-logs.csv
# camera-*-audit-logs.csv
# sensor-*-*-logs.csv

if CorrectObvName:
    for testID, clientTestDir in enumerate(ClientTestDirs):
        print('{}/{} -{} - Started'.format(testID + 1, clientTestDir, len(ClientTestDirs)))

        for appPort in SensorSendPorts:

            clientSensorLogDF = pd.read_csv(clientTestDir + 'sensor-15_181_49_254-{}-logs.csv'.format(appPort))
            clientSensorLogDF['ObservationID'] = clientSensorLogDF['ObvservationID']
            del clientSensorLogDF['ObvservationID']
            clientSensorLogDF.to_csv(clientTestDir + 'sensor-15_181_49_254-{}-logs.csv'.format(appPort))


if False:

    for testID, clientTestDir in enumerate(ClientTestDirs):
        print('{}/{} -{} - Started'.format(testID + 1, clientTestDir, len(ClientTestDirs)))
        serverTestDir = ServerTestDirs[testID]

        mfrLogs = glob.glob(clientTestDir + 'xr90-mobile-logs.csv')

        mfrLogDF = pd.read_csv(mfrLogs[0])

        # Add an epoch timestamp
        epochTimes = []
        udtTimestamps = []

        for rowIDX, row in mfrLogDF.iterrows():
            if CorrectCDT:
                timePriorToConversion = datetime.strptime(row['Log-Date-Time'], DateTimeFormat) - timedelta(hours=5)
            else:
                timePriorToConversion = datetime.strptime(row['Log-Date-Time'], DateTimeFormat)
            udtTimestamps.append(timePriorToConversion.strftime(DateTimeFormat))
            epochTime = timePriorToConversion.timestamp()
            epochTimes.append(epochTime)

        mfrLogDF['Log-Date-Time'] = udtTimestamps
        mfrLogDF['Log-Date-Time-Epoch'] = epochTimes

        mfrLogDF.to_csv(clientTestDir + 'xr90-mobile-logs.csv', index=False)

        for appPort in SensorSendPorts:

            sensorLogs = glob.glob(clientTestDir + 'sensor-*-{}-logs.csv'.format(appPort))

            if len(sensorLogs) > 0:
                sensorLogDF = pd.read_csv(sensorLogs[0])

                epochTimes = []

                for rowIDX, row in sensorLogDF.iterrows():
                    if CorrectCDT_Tputs:
                        timePriorToConversion = datetime.strptime(row['Send-Timestamp'], DateTimeFormat) - timedelta(hours=5)
                    else:
                        timePriorToConversion = datetime.strptime(row['Send-Timestamp'], DateTimeFormat)

                    epochTimes.append(timePriorToConversion.timestamp())

                sensorLogDF['Send-Timestamp-Epoch'] = epochTimes
                sensorLogDF.to_csv(clientTestDir + 'sensor-15_181_49_254-{}-logs.csv'.format(appPort), index=False)
