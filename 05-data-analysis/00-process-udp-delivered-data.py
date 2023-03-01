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
#ServerTestDirs = glob.glob('../../../Datasets/server-data/test-dir/output/*/')
ServerTestDirs = glob.glob('./lidar_metrics/output/client/*/')
TmpDirectory = '../../../Datasets/tmp/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
DateTimeFormat2 = '%Y-%m-%d %H:%M:%S.%f'
# '2379','2380','2381','8319','8320','8321'
SensorSendPorts = ['6001', '6002', '6003', '6004']
#SensorSendPorts = ['2380']
# '2379',
TagLength = 25

# =============================================================
# Debugging Flags


# =============================================================
ServerTestDirs.sort(reverse=True)
# =============================================================

for testID, serverTestDir in enumerate(ServerTestDirs):

    # =============================================================
    # If Camera frames and videos available, figure out bitrates per video samples and per-frame timings
    print('{}/{} - Started {}'.format(testID + 1, len(ServerTestDirs), serverTestDir))

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

            dataLogFileFP = open(serverTestDir + '{}-post-process-logs.csv'.format(sensorPort), 'w')
            dataLogFileFP.write(
                'ObservationID,PartID,Receive-Timestamp(s),Epoch-Receive-Timestamp(s),Length-Of-Chunk-Received(Bytes)\n')
            dataLogFileFP.flush()

            retainedServerTags = []
            retainedServerReceiveTimes = []
            retainedBytes = None

            for rowIDX, row in sensorAuditLogDF.iterrows():
                readAmount = row['Length-Of-Chunk-Received(Bytes)']
                readdataChunk = sensorDataFP.read(readAmount)

                if retainedBytes is not None:
                    # append the read data to the retained to continue the parse
                    dataChunk = retainedBytes[:] + readdataChunk[:]
                else:
                    dataChunk = readdataChunk

                # Read the serverTag, append it to the overall list incase this time has touched another ctag
                recvTag = sensorDataFP.read(row['Tag-Length(Bytes)'])
                recvDateRaw = recvTag.decode().replace('#!#', '')
                epochTime = datetime.strptime(recvDateRaw, DateTimeFormat).timestamp()
                retainedServerTags.append('{}'.format(epochTime))
                retainedServerReceiveTimes.append(recvDateRaw)

                # Go through each "complete Client tag" bounded sent data
                continueUnpacking = True

                while continueUnpacking:
                    tagStartIndex = dataChunk.find(b'#!#')
                    #tagMiddleIndex = dataChunk.find(b'#!#', tagStartIndex + 1)
                    tagMiddleIndex = tagStartIndex + 8 + 3 # 8 bytes, 3 for buffer
                    #tagEndIndex = dataChunk.find(b'#!#', tagMiddleIndex + 3)
                    tagEndIndex = tagMiddleIndex + 8 + 3
                    tagBytes = dataChunk[tagStartIndex:tagEndIndex + 3]
                    serverTagEndIndex = tagEndIndex + 3

                    if len(tagBytes) == TagLength:
                        # Tag present, save out data and truncate the datachunk
                        partIDComponent = dataChunk[tagStartIndex + 3:tagMiddleIndex]
                        obvIDComponent = dataChunk[tagMiddleIndex + 3:tagEndIndex]

                        partID = int.from_bytes(partIDComponent, 'big')
                        observationID = int.from_bytes(obvIDComponent, 'big')

                        # ================

                        segmentChunk = dataChunk[:tagStartIndex]

                        if False:
                            # Write each datachunk out for later concatenation
                            dataChunkFP = open(TmpDirectory + '{}-{}.segment'.format(observationID, partID), 'wb')
                            dataChunkFP.write(segmentChunk)
                            dataChunkFP.flush()
                            dataChunkFP.close()

                        dataLogFileFP.write(
                            '{},{},{},{},{}\n'.format(observationID, partID, retainedServerReceiveTimes[0], retainedServerTags[0], len(segmentChunk)))
                        dataLogFileFP.flush()

                        # remove the relevant length from the overall datachunk
                        dataChunk = dataChunk[serverTagEndIndex:]

                        if len(dataChunk) > 0:
                            retainedChunk = dataChunk
                        else:
                            retainedChunk = None
                            retainedServerTags.clear()
                            retainedServerReceiveTimes.clear()

                    else:
                        # Tag not present, set retained data and goto next read
                        continueUnpacking = False
                        retainedChunk = dataChunk

            dataLogFileFP.close()
            sensorDataFP.close()

            if False:

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
                        observationFP = open(
                            serverTestDir + '{}-obvs/'.format(sensorPort) + '{}.obv'.format(observation), 'wb')

                        for segmentFile in segmentFiles:
                            print('Combining Segment {}'.format(segmentFile))
                            segmentFileFP = open(segmentFile, 'rb')

                            segmentData = segmentFileFP.read()

                            segmentFileFP.close()

                            observationFP.write(segmentData)
                            observationFP.flush()

                        observationFP.flush()
                        observationFP.close()