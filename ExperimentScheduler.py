

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
                    type=str)
parser.add_argument("-fl",
                    "--FileList",
                    dest="FileList",
                    help="File containing a list of specification files that should be processed one after the other.",
                    type=str)
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

###################################
#   Processing Argunments
#

args = vars(parser.parse_args())

if not args["SeriesSpecFile"] == None:
    seriesSpecificationFiles = [args["SeriesSpecFile"]]
else:
    seriesSpecificationFiles = []

    with open(args["FileList"],"r") as file:
        for line in file:
            seriesSpecificationFiles.append(line[:-1]) #[:-1] to remove the \n at the end.
            

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
 
# List of seeds for random Seeding of the Experiment.
if "SeedList" in args:

    seedList = args["SeedList"]

    seeds = []

    with open(seedList,'r') as file:
        for line in file:
            seeds.append(int(line))

###################################
#   Main Scheduling Method (It is that way due to historical groth of this file. It is not pretty)
#

def getCurrentTime():
    return "["+str(datetime.datetime.now())+"] "

def log(folder,file,message,header):
    os.makedirs(folder,exist_ok=True)
    with open(folder+file,'a') as file:
        
        header =  getCurrentTime()+" "+header+"\n"
        file.write(header)
        file.write(str(message)+"\n")

def scheduleExperiments(seriesSpecificationFile,
                        seeds,
                        stopTimeSet,
                        stopTime,
                        muteOutput,
                        ): 
    # Json File specifying the command to run to start an experiment and the arguments involved
    memFile = seriesSpecificationFile+".mem"

    with open(seriesSpecificationFile,'r') as file:
        seriesSpecification = json.load(file)
    
    expStdOutput = "experimentSchedulerLog/experimentOutput/"
    expErrOutput = "experimentSchedulerLog/experimentError/"

    if "StdLogFolder" in seriesSpecification: 
        expStdOutput = seriesSpecification["StdLogFolder"]
        if expStdOutput[-1] == "/":
            expStdOutput += "/"
    if "ErrLogFolder" in seriesSpecification: 
        expErrOutput = seriesSpecification["ErrLogFolder"]
        if expErrOutput[-1] == "/":
            expErrOutput += "/"


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
        firstRun = True


        for pSet in possibleParameters:
            n = len(pSet)
            
            if firstRun:
                for i in range(0,nVariations):
                    parameterIndices.append([i%n])
            else:
                for i in range(0,int(nVariations/changeRate)):
                    for j in range(0,changeRate):
                        parameterIndices[i*changeRate+j].append(int(i%n))
            firstRun = False
            changeRate *= n

        return parameterIndices


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
            if memory[toRun]["#ExperimentsRun"]>2: # Mandatory to have stdev and average runtime for heuristics
                if timeLeft-memory[toRun]["AvgWallTime"] < memory[toRun]["WallTimeStdev"]:

                    deltaTimeLeft = abs(timeLeft-memory[toRun]["AvgWallTime"])                
                    adaptedScheduling = False

                    for key in memory:
                        if memory[key]["#ExperimentsRun"]<=2:
                            break
                        delta = abs(timeLeft-memory[key]["AvgWallTime"])                        
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
        
        
        runCommandNoSeed = copy.copy(runCommand)
        commandArgsNoSeed = copy.copy(commandArgs)#for the file name for logging

        if "RequiresSeed" in seriesSpecification and seriesSpecification["RequiresSeed"] == True:
            seed = seeds[memory[toRun]["#ExperimentsRun"]]
            commandArgs.insert(seriesSpecification["SeedArgumentPosition"]-1,str(seed))

        for arg in commandArgs:
            runCommand += " "+arg
        
        for arg in commandArgsNoSeed:
            runCommandNoSeed += "_"+arg
        #running the experiment
        experimentStartTime = time.time()
        
        if not muteOutput:
            print(getCurrentTime()+" : Running : "+runCommand)

        result = subprocess.run([runCommand],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True,
                                 text=True)

        experimentEndTime = time.time()

        logFileName = runCommandNoSeed
        logFileName = logFileName.replace(" ","_")
        logFileName = logFileName.replace("/",".")
        logFileName+=".log"
        
        if not result.stdout == "":    
            log(expStdOutput,logFileName,result.stdout,"On running "+runCommand+":")
        if not result.stderr == "":    
            log(expErrOutput,logFileName,result.stderr,"On running "+runCommand+":")

        wallTime = experimentEndTime-experimentStartTime

        #updating the memory
        memory[toRun]["CumWallTime"] += wallTime
        memory[toRun]["WallTimes"].append(wallTime)
        
        #Check if there is a criterion for succsess
        if "SuccsessCriterion" in seriesSpecification:
            theCommandArgs = "" 
            for args in commandArgs:
                theCommandArgs += " "+args

            result = subprocess.run([seriesSpecification["SuccsessCriterion"]+theCommandArgs],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True,
                                    text=True)
            
            succsessful = bool(int(result.stdout))

            if succsessful:
                memory[toRun]["#ExperimentsRun"] += 1
                if not muteOutput:
                    print("Met Succsess Criterion at "+runCommand)
            else:
                if not muteOutput:
                    print("Havn't met Succsess Cirterion at "+runCommand)
        else:
            memory[toRun]["#ExperimentsRun"] += 1


        if memory[toRun]["#ExperimentsRun"] >= 2:
            memory[toRun]["AvgWallTime"] = numpy.average(memory[toRun]["WallTimes"])
            memory[toRun]["WallTimeStdev"] = numpy.std(memory[toRun]["WallTimes"])

        with open(memFile,'w') as file:
            json.dump(memory,file)

##########################################
#   The Execution of everything:
#
for f in seriesSpecificationFiles:
    if stopTimeSet:
        timeLeft = (stopTime - datetime.datetime.now()).total_seconds()
    else:
        timeLeft = 1

    if timeLeft > 0:
        print("Start Running "+f)
        scheduleExperiments(f,seeds,stopTimeSet,stopTime,muteOutput)
    else:
        break
