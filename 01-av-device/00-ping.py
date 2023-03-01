import subprocess
import time
import datetime
import sys
import math
from datetime import timezone
import signal

# ========================================
TargetIP = sys.argv[1]
# ========================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'

# ========================================

ContinueToLoop = True
Proc:subprocess.Popen = None

try:
    sampleTime = datetime.datetime.now(timezone.utc)

    Proc = subprocess.Popen(' '.join(['ping', TargetIP, '-D', '>>', 'ping-{}-{}.txt'.format(TargetIP.replace('.','-'),sampleTime.strftime(DateTimeFormat))]), universal_newlines=False, shell=True)
    print('Ping started')

    Proc.wait()


except KeyboardInterrupt as ex:
    Proc.terminate()
    Proc.wait()
    print('Ending Traceroute')

print('Traceroute Concluded')