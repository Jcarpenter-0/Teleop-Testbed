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
import json

# =============================================================
# Unpack delivered data, but ignore the server "receive timestamps" and instead unpack into complete single file, then parse that for partIDs and obvIDs
# =============================================================
ClientTestDirs = glob.glob('../../../Datasets/client-data/*/output/*/')
ServerTestDirs = glob.glob('../../../Datasets/server-data/*/output/*/')
TmpDirectory = '../../../Datasets/tmp/'
# =============================================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
DateTimeFormat2 = '%Y-%m-%d %H:%M:%S.%f'
SensorSendPorts = ['4000','4001']

# =============================================================
# Debugging Flags


# =============================================================
ClientTestDirs.sort(reverse=True)
ServerTestDirs.sort(reverse=True)

for testID, serverTestDir in enumerate(ServerTestDirs):
    clientTestDir = ClientTestDirs[testID]
    # =============================================================
    # If Camera frames and videos available, figure out bitrates per video samples and per-frame timings
    print('{}/{} - Started'.format(testID + 1, len(ServerTestDirs)))


