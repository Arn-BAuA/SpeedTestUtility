
![](SpeedTestUtility.png)

Some classes I need all the time for speedtesting my code.

## profilingCode.py

This is a quick and dirty class for estimating runtime paremeters in an object oriented fashion. Keep in mind that all the things here like cpu-Time and Memory are based on the interpreter that runs the main process, so numbers may be not trustworthy when working with subprocesses or bindings. What can be used all the time thou is Elapsed time.

### Example:

You can Profile your task using the profiler code as follows:

<pre><code>
#!/bin/python

from SpeedTestUtility.profilingCode import profiler

def myTaskToProfile(nRepetitions = 1e6):
	i = 1
	for j in range(0,nRepetitions):
		i+= 1
	
	#The Tasks that are profiled can return a Dict with parameters that will be logged by the profiler:
	pDict = {"Workload":nRepetitions,"SomeParameter":1337,"SomeRandomSeed",12345678}
	return pDict

p = profiler(myTaskToProfile,"Path/to/Store/Outcomes.csv")
p.measure() #here is where the task gets executed and measured.

</code></pre>

Running the following code will automatically create a .csv file with all the parameters.

## ExperimentScheduler.py

This is a code to run Experiments. It automatically keeps track of different experiments and logs what has already been done. This way, if a sereis of experiments gets interrupted, say because someone needs the computer for something else, the scheduler automatically starts at the last recorded checkpoint.<br>
Since the scheduler keeps track how many instances of it are running on the machine, it can also be used in combination with cron. You can also set a stoptime at which experiments should come to an end. This way, the code can be used in conjunction with cron to e.g. use a workstation that is used in the office at daytime as an additional compute resource at night time.<br>

### Simple Example Experiment Setup:

Our dummy experiment code for the test is:

<pre><code>

#Demo code for the test of the scheduler.

import sys
import time
import os

timeToSleep = float(sys.argv[1])
seed = int(sys.argv[2])
multiplicator = int(sys.argv[3])

# This here would be the actual experiment.

for i in range(0,multiplicator):
    time.sleep(timeToSleep)

# Here would be the end of the experiment.

savePath = "testExperiment/outputFile.csv"
line = str(timeToSleep)+","+str(multiplicator)+","+str(seed)+"\n"

with open(savePath,'a') as file:
    file.write(line)


</code></pre>

The code is located in a folder 'testExperiment' relativ to this dict. The code illustrates how experimets should be structured to work with the scheduler. It has three sections. One takes arguments that specify the parameters that are varied in this experiment. The second is than the calculation or the execution of the experiment. In this example we just wait for some time, in some instances multiple times to have a second parameter. In the last Section we save our results. In this case, since the experiment doesnt return anything, we just save parameters.<br>
When the file is ran:

<pre><code>
python testExperiment/experiment.py 1 1200112343 1
</code></pre>

it produces a file testExperiment/outputFile.csv or appends to this file, if present.<br>
This file is now accompanied by a .json file:

<pre><code>

</code></pre>


### Example Setup with Cron:
