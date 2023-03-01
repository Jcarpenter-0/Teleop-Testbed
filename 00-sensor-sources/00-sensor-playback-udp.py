import numpy as np
import sys
import time
import socket
import datetime
import zlib
import math
from datetime import timezone


# ==================================================
# Load in a file of sensor data (as a blob)
# Annotate with Part ID, Obv ID
# Log the Part ID, Obv ID, and Send Time
# This is intended to function as the "sensor" generating and sending data
# An OBU can be targeted to facilitate a "full" pipeline
# ==================================================

# Datafile to read in, if left blank, will "generate" a "flat" blob of all 1s
SensorDataFilePath = sys.argv[1]
if '.txt' in SensorDataFilePath or '.csv' in SensorDataFilePath:
    SensorDataFP = open(SensorDataFilePath, 'r')
else:
    SensorDataFP = open(SensorDataFilePath, 'rb')
# Read this many bytes, this constitutes one "observation" or complete application level unit of information
# Note, this will be broken up into parts if beyond the send size
ReadSizeBytes = int(sys.argv[2])
#Optional Padding of bytes
PaddingBytes = int(sys.argv[3])
# RSend this many bytes, then send it over (must be less than MTU of 1500, likely going to be 1440 or less)
SendSizeBytes = int(sys.argv[4])
# Send the read in bytes at intervals of this rate (eg: X bytes every sendrate seconds)
SendRateSeconds = float(sys.argv[5])
# Target to send Data to
SendTargetIP = sys.argv[6]
SendTargetPort = int(sys.argv[7])

# Optional Args ~ Specifically the compress arg
CompressObservations = int(sys.argv[8])
DropObvservationRate = int(sys.argv[9])

# Constants/Setup
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
#CurrentTime = datetime.datetime.now().strftime(DateTimeFormat)
LogFileFP = open('./sensor-{}-{}-logs.csv'.format(SendTargetIP.replace('.','_'),SendTargetPort),'w')
LogFileFP.write('ObservationID,PartID,Send-Timestamp,Send-Timestamp-Epoch,Compression Time (microseconds),Raw Obv Size(bytes),Compressed Obv Length (bytes),Packet Size(bytes),PacketSendSize(Bytes),TagLength(Bytes),Network Sent\n')
LogFileFP.flush()

# State Tracking
Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Send = True
CurrentPartID = 0
CurrentObvID = 0
ObvCompressTimeStart = None
ObvCompressTimeStop = None
NetworkSendTime = None
CompressTime = None
try:
    while Send:

        if '.txt' in SensorDataFilePath or '.csv' in SensorDataFilePath:
            observation = SensorDataFP.readline().encode()
        else:
            observation = SensorDataFP.read(ReadSizeBytes)

        readLen = len(observation)

        if len(observation) <= 0:
            # Loop file
            SensorDataFP.seek(0,0)
        else:

            if PaddingBytes > 0:
                observation = observation[:] + bytes([1] * PaddingBytes)[:]

            Sent = True

            # Check for drop
            if DropObvservationRate != 0 and CurrentObvID % DropObvservationRate == 0:
                Sent = False
            else:
                # Check for compression
                if CompressObservations == 1:
                    ObvCompressTimeStart = datetime.datetime.now()
                    observation = zlib.compress(observation)
                    ObvCompressTimeStop = datetime.datetime.now()

                # Load and process Data
                sendChunks = []

                SubChunks = math.ceil((len(observation)) / SendSizeBytes)

                if len(observation) > SendSizeBytes and SubChunks > 0:
                    # Obv is too big, must split and send over
                    sendChunks = [observation[i * SendSizeBytes:(i + 1) * SendSizeBytes] for i in range((len(observation) + SendSizeBytes - 1) // SendSizeBytes)]
                else:
                    sendChunks.append(observation)

                # Log, tag, and send the data
                for chunk in sendChunks:
                    # Set the
                    tag = '#!#'.encode()[:] + CurrentPartID.to_bytes(8, 'big')[:] + '#!#'.encode()[:]\
                               + CurrentObvID.to_bytes(8, 'big')[:] + '#!#'.encode()[:]
                    data = chunk[:] + tag[:]

                    # Send the data
                    try:
                        Socket.sendto(data, (SendTargetIP, SendTargetPort))
                        NetworkSendTime = datetime.datetime.now(timezone.utc)
                    except Exception as ex:
                        print('Cannot send.')
                        print(ex)
                        Sent = False

                    # Log the data
                    if ObvCompressTimeStart is not None:
                        CompressTime = (ObvCompressTimeStop - ObvCompressTimeStart).microseconds

                    networkSendTimeString = None
                    networkSendtimeEpoch = None

                    if NetworkSendTime is not None:
                        networkSendTimeString = NetworkSendTime.strftime(DateTimeFormat)
                        networkSendtimeEpoch = NetworkSendTime.timestamp()

                    LogFileFP.write('{},{},{},{},{},{},{},{},{},{},{}\n'.format(CurrentObvID,CurrentPartID,networkSendTimeString,networkSendtimeEpoch,CompressTime,readLen,len(observation),SendSizeBytes,len(data), len(tag),Sent))
                    LogFileFP.flush()

                    CurrentPartID += 1

            # Wait to send next
            time.sleep(SendRateSeconds)
            CurrentObvID += 1

except KeyboardInterrupt as ex:
    Socket.close()
    LogFileFP.close()