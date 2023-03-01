import socket
import os
import psutil
import shutil
import subprocess

# ==================================================
IngestIP = ''
IngestPort = 7000
# ==================================================

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((IngestIP, IngestPort))
sock.listen(1)
print('Control Server: Listening on {}:{}'.format(IngestIP, IngestPort))

testProc:subprocess = None
conn = None

try:
    while True:
        print('Waiting for new test paramaeters')
        conn, addr = sock.accept()

        data = conn.recv(1000)

        if len(data) > 0:
            # Assume start command for now
            profilePath = data.decode()

            print('Prepping Test: {}'.format(profilePath))

            testProc = subprocess.Popen(['python3', './00-driver-client.py', profilePath])

            conn.close()

            testProc.wait()
            print('DAEMON CALLER: Test Process is finished')


except KeyboardInterrupt as ex:
    if conn is not None:
        conn.close()

    if testProc is not None:
        testProc.wait()
        testProc.terminate()