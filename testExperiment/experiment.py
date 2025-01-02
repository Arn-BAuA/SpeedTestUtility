
#Demo code for the test of the scheduler.

import sys
import time
import os

timeToSleep = float(sys.argv[1])
seed = int(sys.argv[2])
multiplicator = int(sys.argv[3])

for i in range(0,multiplicator):
    time.sleep(timeToSleep)

savePath = "testExperiment/outputFile.csv"
line = str(timeToSleep)+","+str(multiplicator)+","+str(seed)+"\n"

with open(savePath,'a') as file:
    file.write(line)

