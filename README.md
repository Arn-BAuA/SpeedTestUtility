# Speed Test Utility

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
