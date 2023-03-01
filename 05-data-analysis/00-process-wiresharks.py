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
ClientTestDirs = glob.glob('../../../Datasets/client-data/*/output/*/')
ServerTestDirs = glob.glob('../../../Datasets/server-data/*/output/*/')
TmpDirectory = '../../../Datasets/tmp/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
DateTimeFormat2 = '%Y-%m-%d %H:%M:%S.%f'
SensorSendPorts = ['4000','4001','4002','4003','4004','4005']

TestTruncationEndTime = 300
TestTruncationStartTime = 1

# =============================================================
# Debugging Flags

PRocessRetransmitts = False
ProcessRTTs = True
ProcessThroughputs = False

# =============================================================
ClientTestDirs.sort(reverse=True)
ServerTestDirs.sort(reverse=True)
# =============================================================

def ProcessWiresharkBytes(traceFile:str, filterString:str='BYTES()udp', timeStart:int=12, timeLimit:int=299) -> dict:
    tsharkProc = subprocess.Popen(
        [" ".join(['tshark', '-r', traceFile, '-q', '-z', 'io,stat,1,\"{}\"'.format(filterString)])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    traceRaw = tsharkProc.stdout.readlines()

    tputs = []

    for rawRow in traceRaw[timeStart + 11:timeLimit]:
        pieces = rawRow.decode().split('|')

        byteAmount = int(pieces[2].strip())

        tputs.append(byteAmount)

    # Get timestamps
    capInfosProc = subprocess.Popen(
        [" ".join(['capinfos', traceFile, '-a'])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    capInfosProc.wait()
    timestampForStart = capInfosProc.stdout.readlines()[-1].decode().replace('\n','').split('  ')[-1].strip()[:-3]
    timeStartObject = datetime.strptime(timestampForStart, '%Y-%m-%d %H:%M:%S.%f')

    #capInfosProc = subprocess.Popen(
    #    [" ".join(['capinfos', traceFile, '-a', '-S'])], stdout=subprocess.PIPE,
    #    stderr=subprocess.PIPE, shell=True)
    #capInfosProc.wait()
    #timestamptEpochForStart = float(capInfosProc.stdout.readlines()[-1].decode().replace('\n','').split(' ')[-1])

    times = []
    timesEpochs = []

    adjustedTimeStartObject = timeStartObject + timedelta(hours=5)

    for secondTimestep in range(len(tputs)):
        timeAdd = adjustedTimeStartObject.timestamp() + secondTimestep
        timesEpochs.append(timeAdd)
        newTimeObject = adjustedTimeStartObject + timedelta(seconds=secondTimestep)
        times.append(newTimeObject.strftime(DateTimeFormat))

    return {"tputs":tputs,"times":times,"times-epochs":timesEpochs}

def ResolveWiresharkPortToRTSPStream(traceFile:str, srcPort:str, dstPort:str='8554') -> str:
    tsharkProc = subprocess.Popen(
        [" ".join(['tshark', '-r', traceFile, '\"tcp.dstport == {} and tcp.srcport == {} and rtsp.request and rtsp.session\"'
                  .format(dstPort, srcPort)])], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    traceRaw = tsharkProc.stdout.readlines()

    try:

        sessionSetup = traceRaw[-1].decode()

        sessionPieces = sessionSetup.split(' ')

        publishURL = sessionPieces[-2]

        cameraName = publishURL.split('/')[-1]
    except Exception as ex:
        print('Error getting RTSP for srcPort {} {}'.format(srcPort, ex))
        cameraName = None

    return cameraName

def GetWiresharkRetransmits(traceFile:str, srcPort:str, outputDir:str) -> dict:
    #

    tsharkCommand = ['tshark', '-r', traceFile, '-Y', '\"tcp.dstport=={} and tcp.analysis.retransmission\"'.format(srcPort), '-T', 'fields', '-E', 'separator=\",\"', '-e', 'frame.time_epoch', '-e', 'tcp.analysis.initial_rtt', '-e', 'tcp.analysis.ack_rtt', '>', '{}{}-retransmits.csv'.format(outputDir,srcPort)]

    tsharkProc = subprocess.Popen(" ".join(tsharkCommand), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    #traceRaw = tsharkProc.stdout.readlines()

    return None

def GetWiresharkRTT(traceFile:str, srcPort:str, outputDir:str) -> None:
    """Get retransmitts"""

    tsharkCommand = ['tshark', '-r', traceFile, '-Y', '\"tcp.srcport=={} and tcp.analysis.ack_rtt\"'.format(srcPort), '-T', 'fields', '-E', 'separator=\",\"', '-e', 'frame.time_epoch', '-e', 'tcp.analysis.initial_rtt', '-e', 'tcp.analysis.ack_rtt', '>', '{}{}-rtts.csv'.format(outputDir,srcPort)]

    tsharkProc = subprocess.Popen(" ".join(tsharkCommand), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    tsharkProc.wait()
    #traceRaw = tsharkProc.stdout.readlines()

    return

for testID, clientTestDir in enumerate(ClientTestDirs):
    serverTestDir = ServerTestDirs[testID]

    # =============================================================
    # If Camera frames and videos available, figure out bitrates per video samples and per-frame timings
    print('{}/{} - Started {}'.format(testID, len(ClientTestDirs)-1, clientTestDir))

    tracefiles = glob.glob(clientTestDir + '*.pcapng')

    if len(tracefiles) > 0:

        if ProcessThroughputs:

            udpData = ProcessWiresharkBytes(tracefiles[0], 'BYTES()udp', timeStart=TestTruncationStartTime,
                                            timeLimit=TestTruncationEndTime)
            tcpData = ProcessWiresharkBytes(tracefiles[0], 'BYTES()tcp', timeStart=TestTruncationStartTime,
                                            timeLimit=TestTruncationEndTime)
            nonData = ProcessWiresharkBytes(tracefiles[0], 'BYTES()not udp and not tcp', timeStart=TestTruncationStartTime,
                                            timeLimit=TestTruncationEndTime)

            tputsDF = pd.DataFrame()
            tputsDF['Timestamp'] = udpData['times']
            tputsDF['Timestamp-Epoch'] = udpData['times-epochs']
            tputsDF['UDP-Bytes'] = udpData['tputs']
            tputsDF['TCP-Bytes'] = tcpData['tputs']
            tputsDF['Nons-Bytes'] = nonData['tputs']
            tputsDF['UDP-Bits'] = np.multiply(udpData['tputs'], 8)
            tputsDF['TCP-Bits'] = np.multiply(tcpData['tputs'], 8)
            tputsDF['Nons-Bits'] = np.multiply(nonData['tputs'], 8)


        for appPort in SensorSendPorts:
            print('Getting Wireshark Data for {}'.format(appPort))
            GetWiresharkRetransmits(tracefiles[0],appPort,clientTestDir)
            GetWiresharkRTT(tracefiles[0],appPort,clientTestDir)

            appName = appPort

            if ProcessThroughputs:
                specificPortUDPTputs = ProcessWiresharkBytes(tracefiles[0], 'BYTES()udp.dstport == {}'.format(appPort),
                                                             timeStart=TestTruncationStartTime,
                                                             timeLimit=TestTruncationEndTime)
                specificPortTCPTputs = ProcessWiresharkBytes(tracefiles[0], 'BYTES()tcp.dstport == {}'.format(appPort),
                                                             timeStart=TestTruncationStartTime,
                                                             timeLimit=TestTruncationEndTime)

                tputsDF['UDP-{}-Bytes'.format(appName)] = specificPortUDPTputs['tputs']
                tputsDF['TCP-{}-Bytes'.format(appName)] = specificPortTCPTputs['tputs']
                tputsDF['UDP-{}-Bits'.format(appName)] = np.multiply(specificPortUDPTputs['tputs'], 8)
                tputsDF['TCP-{}-Bits'.format(appName)] = np.multiply(specificPortTCPTputs['tputs'], 8)

        if ProcessThroughputs:
            tputsDF.to_csv(clientTestDir + 'throughputs.csv', index=False)
    else:
        print('{} has no wireshark!'.format(clientTestDir))


