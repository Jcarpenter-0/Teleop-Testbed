import os
import sys
import subprocess
import time

# ===============================================
# Auto run tests given in lists
# ===============================================
TestsPath = sys.argv[1]
InterTestTime = 20
# ===============================================
testsFP = open(TestsPath, 'r')
tests = testsFP.readlines()
testsFP.close()

# ===============================================
testProc = None

try:
    print('Starting pattern {}'.format(TestsPath))
    for testNum, test in enumerate(tests):
        test = test.replace('\n','')
        print('{}/{} Starting profile {}'.format(testNum,len(tests)-1,test))
        testProc = subprocess.Popen(['python3', '01-av-device.py', test])
        testProc.wait()
        # clear screen, it can overload the phone
        os.system('reset')
        print('Profile {} done, waiting for server to end (20 seconds)'.format(test))
        time.sleep(InterTestTime)

    print('Pattern {} done'.format(TestsPath))

except KeyboardInterrupt as ex:

    if testProc is not None:
        testProc.wait()
        testProc.terminate()