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
# Unpack delivered data, but ignore the server "receive timestamps" and instead unpack into complete single file, then parse that for partIDs and obvIDs
# =============================================================
ClientTestDirs = glob.glob('../../../Datasets/client-data/*/output/*/')
ServerTestDirs = glob.glob('../../../Datasets/server-data/*/output/*/')
TmpDirectory = '../../../Datasets/tmp/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
DateTimeFormat2 = '%Y-%m-%d %H:%M:%S.%f'
SensorSendPorts = ['4002','4003','4004','4005']
ManualReadSizes = [504, 426, 717, 190]
TagLength = 25

# =============================================================
# Debugging Flags


# =============================================================
ClientTestDirs.sort(reverse=True)
ServerTestDirs.sort(reverse=True)

# =============================================================

# =============================================================

for testID, serverTestDir in enumerate(ServerTestDirs):
    clientTestDir = ClientTestDirs[testID]
    # =============================================================
    # If Camera frames and videos available, figure out bitrates per video samples and per-frame timings
    print('{}/{} - Started'.format(testID, len(ServerTestDirs)-1))

    for sensorID, sensorPort in enumerate(SensorSendPorts):

        # Continue onto the sensor data unpack

        sentDataFiles = glob.glob(serverTestDir + 'sensor--{}-tagged-*.data'.format(sensorPort))

        if len(sentDataFiles) <= 0:
            sentDataFiles = glob.glob(serverTestDir + 'sensor-{}-tagged-*.data'.format(sensorPort))

        serverSideAuditLogs = glob.glob(serverTestDir + 'sensor--{}-audit-logs.csv'.format(sensorPort))

        clientSideAuditLogs = glob.glob(clientTestDir + 'sensor-*-{}-logs.csv'.format(sensorPort))

        # Clean up the tmp files for reuse of the directory
        tmpFiles = glob.glob(TmpDirectory + '*')

        for tmpFile in tmpFiles:
            os.remove(tmpFile)

        if len(serverSideAuditLogs) > 0 and len(sentDataFiles) > 0 and len(clientSideAuditLogs) > 0:

            sensorAuditLogDF = pd.read_csv(serverSideAuditLogs[0])
            sensorDataFP = open(sentDataFiles[0], 'rb')

            untaggedRawDataFP = open(serverTestDir + 'sensor--{}-compressed-0.data'.format(sensorPort), 'wb')

            for rowIDX, row in sensorAuditLogDF.iterrows():
                readAmount = row['Length-Of-Chunk-Received(Bytes)']
                readdataChunk = sensorDataFP.read(readAmount)

                # Read the serverTag, dump this, as its not useful for tcp
                recvTag = sensorDataFP.read(row['Tag-Length(Bytes)'])
                recvDateRaw = recvTag.decode().replace('#!#', '')
                epochTime = datetime.strptime(recvDateRaw, DateTimeFormat).timestamp()

                untaggedRawDataFP.write(readdataChunk)
                untaggedRawDataFP.flush()

            untaggedRawDataFP.close()

            print('Unpacking the {} untagged data'.format(sensorPort))
            # Now, read in the untagged raw data, and get partIDs and the obvIDs, we need strict packet read sizes here
            clientAuditLogDF = pd.read_csv(clientSideAuditLogs[0])
            untaggedRawDataFP = open(serverTestDir + 'sensor--{}-compressed-0.data'.format(sensorPort), 'rb')

            dataLogFileFP = open(serverTestDir + '{}-post-process-logs.csv'.format(sensorPort), 'w')
            dataLogFileFP.write('ObservationID,PartID,Length-Of-Chunk-Received(Bytes)\n')
            dataLogFileFP.flush()

            for rowIDX, row in clientAuditLogDF.iterrows():
                try:
                    targetedReadSize = int(row['PacketSendSize(Bytes)'])
                except:
                    targetedReadSize = ManualReadSizes[sensorID]

                # Read in what should be a full part, we can check this by seeing if a "full" single ctag is present
                currentChunk = untaggedRawDataFP.read(targetedReadSize)

                tagStartIndex = currentChunk.find(b'#!#')
                # tagMiddleIndex = dataChunk.find(b'#!#', tagStartIndex + 1)
                tagMiddleIndex = tagStartIndex + 8 + 3  # 8 bytes, 3 for buffer
                tagEndIndex = currentChunk.find(b'#!#', tagMiddleIndex + 3)
                tagBytes = currentChunk[tagStartIndex:tagEndIndex + 3]
                serverTagEndIndex = tagEndIndex + 3

                if len(tagBytes) == 25:

                    partIDComponent = currentChunk[tagStartIndex + 3:tagMiddleIndex]
                    obvIDComponent = currentChunk[tagMiddleIndex + 3:tagEndIndex]

                    partID = int.from_bytes(partIDComponent, 'big')
                    observationID = int.from_bytes(obvIDComponent, 'big')

                    dataLogFileFP.write('{},{},{}\n'.format(observationID, partID, len(currentChunk)))
                    dataLogFileFP.flush()

            dataLogFileFP.close()

