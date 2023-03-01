import subprocess
import time
import datetime
import sys
import math
from datetime import timezone
import signal

# ========================================
TargetIP = sys.argv[1]
TraceRouteDuration = float(sys.argv[2])
# ========================================
DateTimeFormat = '%y-%m-%d-%H-%M-%S-%f'
MaxHops = '50'

# ========================================

ContinueToLoop = True
Proc:subprocess.Popen = None

try:
    while ContinueToLoop:
        sampleTime = datetime.datetime.now(timezone.utc)

        Proc = subprocess.Popen(' '.join(['traceroute', TargetIP, '-m', MaxHops, '>>', 'traceoute-{}-{}.txt'.format(TargetIP.replace('.','-'),sampleTime.strftime(DateTimeFormat))]), universal_newlines=False, shell=True)
        print('Traceroute Started')

        time.sleep(TraceRouteDuration)

        Proc.terminate()
        Proc.wait()

except KeyboardInterrupt as ex:
    Proc.terminate()
    Proc.wait()

    print('Ending Traceroute')

print('Traceroute Concluded')