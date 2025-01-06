
#Demo code for the test of the scheduler.

import sys
import time
import os

if sys.argv[1] == "--Verify":
    import random

    if(random.random()>0.5):
        print(1,end="")
    else:
        print(0,end="")
    sys.exit()

timeToSleep = float(sys.argv[1])
seed = int(sys.argv[2])
multiplicator = int(sys.argv[3])

if multiplicator == 3:
    raise Exception("Multiplicator of 3 not allowed.")

for i in range(0,multiplicator):
    print("Waiting for "+str(timeToSleep))
    time.sleep(timeToSleep)

savePath = "testExperiment/outputFile.csv"
line = str(timeToSleep)+","+str(multiplicator)+","+str(seed)+"\n"

with open(savePath,'a') as file:
    file.write(line)

