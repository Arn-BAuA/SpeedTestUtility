

import numpy
import argparse
import os
import time
import json
import copy
import subprocess
import datetime

#Parsing command line Arguments:
parser = argparse.ArgumentParser()

parser.add_argument("-f",
                    "--SpecificationFile",
                    dest="SeriesSpecFile",
                    help="Json File specifying how one measurement series should look like.",
                    type=str,
                    required=True)
parser.add_argument("-s",
                    "--SeedList",
                    "--Seeds",
                    dest="SeedList",
                    help="A list of seeds, fo r experiments that use seeded random.",
                    type=str)
parser.add_argument("-m",
                    "--mute",
                    "--NoOutput",
                    dest="mute",
                    help="If true, this scirpt doesnt produce output",
                    type = bool,
                    default = False)
parser.add_argument("-t",
                    "--RunUntil",
                    dest="runUntil",
                    help="Requires a time in military time in the format hh:mm or a date in yyyy-MM-dd,hh:mm. If set, the code tries to schedule experiments in a way that they finish round about the time that is specified. Estimation is based on already conducted experiments. This is for the use in conjunction with cron.",
                    type=str)
parser.add_argument("-tt",
                    "--time-table",
                    dest="TimeTable",
                    help="Requires a json like time table. If specified, the next time the script should terminate will be read from the timetable.",
                    type=str)
parser.add_argument("-i",
                    "--instanceHandling",
                    dest="InstanceHandling",
                    help="either 'wait','startAnyway','dontStart'. If a nother instance of the process is running, this instance does the specified. it will either wait for the other instance to finish and than start, start anyway in paralell or will not start (the call will be ignored)",
                    default="wait",
                    type=str)

args = vars(parser.parse_args())

# Json File specifying the command to run to start an experiment and the arguments involved
seriesSpecificationFile = args["SeriesSpecFile"]
memFile = seriesSpecificationFile+".mem"

with open(seriesSpecificationFile,'r') as file:
    seriesSpecification = json.load(file)


# List of seeds for random Seeding of the Experiment.
if seriesSpecification["RequiresSeed"]:
    if not "SeedList" in args:
        raise Exception("A seedlist is required to run "+args["SeriesSpecFile"]+".")

    seedList = args["SeedList"]

    seeds = []

    with open(seedList,'r') as file:
        for line in file:
            seeds.append(int(line))

muteOutput = args["mute"]

stopTimeSet = False
stopTime = None

if not args["runUntil"] == None:
    stopTimeSet = True

    timeAsStr = args["runUntil"]

    parseError= False
    
    if len(timeAsStr) <= 5:
        #it is hh:mm
        t = datetime.time.fromisoformat(timeAsStr)

        currentDateTime = datetime.datetime.now()
        currentTime = currentDateTime.time()
        currentDate = currentDateTime.date()

        if currentTime > t:
            #Date is next day.
            delta = datetime.timedelta(days=1)
            stopTime = datetime.datetime.combine(currentDate+delta,t)
        else:
            #Date is this day
            stopTime = datetime.datetime.combine(currentDate,t)

if not args["TimeTable"] == None:
    with open(args["TimeTable"],'r') as file:
        JsonTimeTable = json.load(file)
    
    conversionTable = {
                "monday":0,
                "tuesday":1,
                "wednesday":2,
                "thursday":3,
                "friday":4,
                "saturday":5,
                "sunday":6,
                }
    
    timeTable = {};
    for key in JsonTimeTable:
        timeTable[conversionTable[key]] = JsonTimeTable[key]

    currentDateTime = datetime.datetime.now()
    currentWeekday = currentDateTime.date().isoweekday()-1
    
    deltaDays = 0
    nextStoptimeFound = False

    while not nextStoptimeFound:
        dayToCheck = (currentWeekday+deltaDays)%7
        
        if dayToCheck in timeTable:
            t = datetime.time.fromisoformat(timeTable[dayToCheck])
            if deltaDays == 0:
                if t<currentDateTime.time():
                    deltaDays += 1
                    continue; #this means it is the right day, but the stopping date has already passed.

            delta = datetime.timedelta(days = deltaDays)

            stopTime = datetime.datetime.combine(currentDateTime.date()+delta,t)
            stopTimeSet = True
            nextStoptimeFound = True
            break;

        deltaDays += 1


if stopTimeSet:
    print("Stop Time is set to "+str(stopTime))

#Keys used to remember Run.
def createExperimentKey(parameterIndices):
    key = ""
    for i,index in enumerate(parameterIndices):
        key += "p"+str(i)+":"+str(index)+";"
    return key

def getAllParameterVariations(possibleParameters):
    parameterIndices = []
    
    nVariations = 1

    for pSet in possibleParameters:
        nVariations *= len(pSet)

    changeRate = 1

    for pSet in possibleParameters:
        n = len(pSet)
        
        if changeRate == 1:
            for i in range(0,nVariations):
                parameterIndices.append([i%n])
        else:
            for i in range(0,int(nVariations/changeRate)):
                for j in range(0,changeRate):
                    parameterIndices[i*changeRate+j].append(int(i%n))
        
        changeRate *= n

    return parameterIndices

def getCurrentTime():
    return "["+str(datetime.datetime.now())+"] "

memory = {}

#Load List of experiments
if os.path.exists(memFile):
    with open(memFile,'r') as file:
        memory = json.load(file)

#Update List (In Case additional Parameters are added to the series File ...)
variations = getAllParameterVariations(seriesSpecification["Variations"])
updateOccured = False


for v in variations:
    key = createExperimentKey(v)
    if not key in memory:
        memory[key] = {
                    "ParameterIndices":v,
                    "CumWallTime":0,
                    "WallTimes":[],
                    "AvgWallTime":0,
                    "WallTimeStdev":0,
                    "#ExperimentsRun":0,
                }
        updateOccured = True

if updateOccured:
    with open(memFile,'w') as file:
        json.dump(memory,file)


allDone = False

while not allDone:
    #Check if we are done
    for key in memory:
        allDone = True;
        if not memory[key]["#ExperimentsRun"] == len(seeds):
            allDone = False
            break
    
    if allDone:
        if not muteOutput:
            print(getCurrentTime()+": All Done Here.")
        break

    #Determine next experiment to be ran:
    
    ranTheLeast = ""
    cumTime = float("inf")

    for key in memory:
        if memory[key]["CumWallTime"] < cumTime:
            if not memory[key]["#ExperimentsRun"] == len(seeds):
                ranTheLeast = key
                cumTime = memory[key]["CumWallTime"]


    toRun = ranTheLeast
    
    if stopTimeSet:
        timeLeft = (stopTime - datetime.datetime.now()).total_seconds()
        
        if timeLeft < 0:
            if not muteOutput:
                print(getCurrentTime()+": Stopping code Execution (Set Stop Time is reached)")
            break;
       #TODO: The following heuristics is lazy. In theory, scheduling could be adapted to reach stop more or less exactly at the specified time. How every, for the problem to be solved exactly, one needs to solve the binpacking problem. We can create some heuristics for scheduling here... 
       #I am also not 100% sure this works. Have not tested it.
        if memory[toRun]["#ExperimentsRun"]>2:
            if timeLeft-memory[toRun]["AverageWallTime"] < memory[toRun]["WallTimeStdev"]:

                deltaTimeLeft = abs(timeLeft-memory[toRun]["AverageWallTime"])                
                adaptedScheduling = False

                for key in memory:
                    delta = abs(timeLeft-memory[key]["AverageWallTime"])                        
                    if delta < deltaTimeLeft:
                        deltaTimeLeft = delta
                        toRun = key
                        adaptedScheduling = True

                    if adaptedScheduling and not muteOutput:
                        print(getCurrentTime()+": Adapted Scheduling to meet Stop Time.")

        


    #Creating Call command for the Experiment

    runCommand = seriesSpecification["Command"]
    commandArgs = []
    for i,index in enumerate(memory[toRun]["ParameterIndices"]):
        commandArgs.append(str(seriesSpecification["Variations"][i][index]))

    if "RequiresSeed" in seriesSpecification and seriesSpecification["RequiresSeed"] == True:
        seed = seeds[memory[toRun]["#ExperimentsRun"]]
        commandArgs.insert(seriesSpecification["SeedArgumentPosition"]-1,str(seed))

    for arg in commandArgs:
        runCommand += " "+arg

    #running the experiment
    experimentStartTime = time.time()
    
    if not muteOutput:
        print(getCurrentTime()+" : Running : "+runCommand)

    subprocess.call(runCommand,shell=True)

    experimentEndTime = time.time()

    wallTime = experimentEndTime-experimentStartTime

    #updating the memory
    memory[toRun]["CumWallTime"] += wallTime
    memory[toRun]["WallTimes"].append(wallTime)
    memory[toRun]["#ExperimentsRun"] += 1
    if memory[toRun]["#ExperimentsRun"] >= 2:
        memory[toRun]["AvgWallTime"] = numpy.average(memory[toRun]["WallTimes"])
        memory[toRun]["WallTimeStdev"] = numpy.std(memory[toRun]["WallTimes"])

    with open(memFile,'w') as file:
        json.dump(memory,file)
