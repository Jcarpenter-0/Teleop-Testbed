import glob
import sys
import socket
import datetime
from datetime import timezone

# ============================================================
# Receive sensor data, dump it to file as directly as possible
# Post-processing will decompress (if needed) then analyze the QoE and QoS values
# ============================================================
IngestIP = ''
PacketSize = int(sys.argv[1])
IngestPort = int(sys.argv[2])
Compressed = int(sys.argv[4])
# ==========================================================

# Constants/setup

DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
CurrentTime = datetime.datetime.now(timezone.utc).strftime(DateTimeFormat)
LogFileFP = open('./sensor-{}-{}-audit-logs.csv'.format(IngestIP.replace('.','_'),IngestPort),'w')
LogFileFP.write('Receive-Timestamp,Receive-Timestamp-Epoch,Length-Of-Chunk-Received(Bytes),Tag-Length(Bytes),Tagged-DataSize(Bytes)\n')
LogFileFP.flush()
RawDataOutputFile = './sensor-{}-{}-tagged-compressed-{}.data'.format(IngestIP.replace('.','_'),IngestPort,Compressed)
RawDataOutputFP = open(RawDataOutputFile, 'wb')

# State management
Socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
Socket.bind((IngestIP, IngestPort))

print('Sensor UDP Server Up {}'.format(IngestPort))

try:
    while True:
        data, addr = Socket.recvfrom(PacketSize * 1280)

        recvTime = datetime.datetime.now(timezone.utc)

        dataLength = len(data)

        recvTag = '#!#'.encode()[:] + recvTime.strftime(DateTimeFormat).encode()[:] + '#!#'.encode()[:]

        tagLength = len(recvTag)

        # Append an additional "recv time" data piece
        chunk = data[:] + recvTag[:]

        RawDataOutputFP.write(chunk)
        RawDataOutputFP.flush()

        LogFileFP.write(
            '{},{},{},{},{}\n'.format(recvTime,recvTime.timestamp(), dataLength, tagLength,len(chunk)))
        LogFileFP.flush()

except KeyboardInterrupt as ex:
    Socket.close()
    LogFileFP.close()
    RawDataOutputFP.close()