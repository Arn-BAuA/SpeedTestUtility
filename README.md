
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
This file is now accompanied by a .json file (testSeries.json):

<pre><code>
{
	"Command":"python testExperiment/experiment.py",
	"RequiresSeed":true,
	"SeedArgumentPosition":2,
	"Variations":[
		[1,1.5,2.5],
		[1,2]
	],
	"StdLogFolder":"testExperiment/log/Exp2/Output/",
	"ErrLogFolder":"testExperiment/log/Exp2/Errors/"
}
</code></pre>

StdLogFolder and ErrLogFolder indicate where the outputs of the experiment processes should be stored. If the folders don't exist they will be created if needet.

THis file specifies which parameter should be varried. If we now call:

<pre><code>
python ExperimentScheduler.py -f testExperiment/testSeries.json -s testExperiment/seedList.txt 
</code></pre>

The code produces the follwoing output:

<pre><code>
python testExperiment/experiment.py 1 12345678 1
python testExperiment/experiment.py 1.5 12345678 1
python testExperiment/experiment.py 2.5 12345678 1
python testExperiment/experiment.py 1 12345678 2
python testExperiment/experiment.py 1.5 12345678 2
python testExperiment/experiment.py 2.5 12345678 2
python testExperiment/experiment.py 1 12345679 1
python testExperiment/experiment.py 1.5 12345679 1
python testExperiment/experiment.py 1 12345679 2
python testExperiment/experiment.py 1 12345680 1
python testExperiment/experiment.py 2.5 12345679 1
python testExperiment/experiment.py 1.5 12345679 2
python testExperiment/experiment.py 1.5 12345680 1
python testExperiment/experiment.py 1 12345680 2
python testExperiment/experiment.py 2.5 12345679 2
python testExperiment/experiment.py 2.5 12345680 1
python testExperiment/experiment.py 1.5 12345680 2
python testExperiment/experiment.py 2.5 12345680 2
All Done Here.
</code></pre>

All the specified parametercombinations are executed. Notice how the code starts to adopt in the later executions. Experiments that take longer to run will be executed less often. This way, information is gathered first there where it is easyest to be obtained.

### Example Setup with Cron:

In addition to the features shown in the previous example, it is possible to set a stoptime for the script. The script will stop automatically when the stoptime is met:

<pre><code>
python ExperimentScheduler.py -f testExperiment/testSeries.json -s testExperiment/seedList.txt -t 14:00
</code></pre>

The specifier -t lets you set a time or date and time when the code stops.
When a specifier is set, the code outputs:

<pre><code>
Stop Time is set to 2025-01-06 14:00:00
</code></pre>

To indicate that the setting worked.

It is also possible to provide a timetable via json:

<pre><code>
{
	"monday":"06:30",
	"tuesday":"06:30",
	"wednesday":"06:30",
	"thursday":"06:30",
	"friday":"06:30"
}
</code></pre>

This is a series of stopdates distributed over the week. If we combine this with a cronjob that starts the code every monday to friday at 18:00 o'Clock, the computer executes the experiments automatically at night.<br>
Time Tables are specified with the -tt flag:
<pre><code>
python ExperimentScheduler.py -f testExperiment/testSeries.json -s testExperiment/seedList.txt -tt testExperiment/timetable.json
</code></pre>

### Scheduling Multiple Experiments:
It is also possible to have a experiments list file that contians the paths of multiple Experiment Json Files:

<pre><code>
testExperiment/testSeries1.json
testExperiment/testSeries2.json
</pre></code>

This can be passed with 

<pre><code>
python ExperimentScheduler.py -fl testExperiment/testExperimentList.txt -s testExperiment/seedList.txt
</code></pre>

The different Experiments are scheduled one after the other. Code from the first experiment will only be executed if every run from the first experiment is already done.

### Designing Experiemts with variable number of runs.

Sometimes one can not know how often something should be ran. E.g. in runtime estimation, it is a quiet common experiment design to give an algorithm a specific time budget and see how large the input is that can be processed in that time.
In such a situation it may occure that one has to try several sizes of input, until the right one is found. The experiment code has roudimentary structures to handle this. <br>
Look at the following json:

<pre><code>
{
	"Command":"python testExperiment/experiment.py",
	"RequiresSeed":true,
	"SeedArgumentPosition":2,
	"Variations":[
		[1,1.5],
		[1,2]
	],
	"StdLogFolder":"testExperiment/log/Exp2/Output/",
	"ErrLogFolder":"testExperiment/log/Exp2/Errors/",
	"SuccsessCriterion":"python testExperiment/experiment.py --Verify"
}
</code></pre>

The line "SuccsessCirterion" defines a method call. In our case it is a modified version of the already known experiment.py:

<pre><code>

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

[....] and so on and so forth.
</code></pre>

SuccsessCriterion should contain the call of a method that, upon recieving the paramteres of the experiment call, can recive if the experiment met the succsess cirterion or if it must be redone. The experiment code must do the alternations for the new attempt by it self. The criterion must return either 0 or 1 on std output to indicate the succsess.

