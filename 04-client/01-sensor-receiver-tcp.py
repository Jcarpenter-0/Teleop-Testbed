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
RawDataOutputFile = './sensor-{}-tagged-compressed-{}.data'.format(IngestPort,Compressed)
RawDataOutputFP = open(RawDataOutputFile, 'wb')

# State management
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((IngestIP, IngestPort))
sock.listen(1)

print('Sensor TCP Server Up {}:{}'.format(IngestIP,IngestPort))

conn, addr = sock.accept()

try:
    while True:
        data = conn.recv(PacketSize * 1280)

        if len(data) > 0:

            recvTime = datetime.datetime.now(timezone.utc)

            dataLength = len(data)

            recvTag = '#!#'.encode()[:] + recvTime.strftime(DateTimeFormat).encode()[:] + '#!#'.encode()[:]

            tagLength = len(recvTag)

            # Append an additional "recv time" data piece
            chunk = data[:] + recvTag[:]

            # write to single blob file
            RawDataOutputFP.write(chunk)
            RawDataOutputFP.flush()

            LogFileFP.write(
                '{},{},{},{},{}\n'.format(recvTime,recvTime.timestamp(), dataLength, tagLength,len(chunk)))
            LogFileFP.flush()

except KeyboardInterrupt as ex:
    conn.close()
    LogFileFP.close()
    RawDataOutputFP.close()