

import sys
import os
import time
import json
import copy
import subprocess

# Json File specifying the command to run to start an experiment and the arguments involved
seriesSpecificationFile = sys.argv[1]
memFile = seriesSpecificationFile+".mem"


# List of seeds for random Seeding of the Experiment.
seedList = sys.argv[2]

#Keys used to remember Run.
def creatExperimentKey(parameterIndices):
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
            for i in range(0,nVariations/changeRate):
                for j in range(0,changeRate):
                    parameterIndices[i*changeRate+j].append(int(i%n))
        
        changeRate *= n

    return parameterIndices


with open(seriesSpecificationFile,'r') as file:
    seriesSpecification = json.load(file)

seeds = []
with open(seedList,'r') as file:
    for line in file:
        seeds.append(int(line))

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
                    "#ExperimentsRun":0,
                }
        updateOccured = True

if updateOccured:
    with open(memFile,'w') as file:
        json.dump(memory,file)


#Determine next experiment to be ran:

ranTheLeast = memory.keys()[0]
cumTime = memory[ranTheLeast]["CumWallTime"]

for key in memory:
    if memory[key]["CumWallTime"] < cumTime:
        ranTheLeast = key
        cumTime = memory[key]["CumWallTime"]

#Creating Call command for the Experiment

runCommand = seriesSpecification["Command"]
commandArgs = []
for i,index in enumerate(memory[ranTheLast]["ParameterIndices"]):
    commandArgs.append(str(seriesSpecification["Variations"][i][index]))

if "RequiresSeed" in seriesSpecification and seriesSpecification["RequiresSeed"] == True:
    seed = seeds[memory[ranTheLast]["#ExperimentsRun"]]
    commandArgs.insert(seriesSpecification["SeedArgumentPosition"],str(seed))

for arg in commandArgs:
    runCommand += " "+arg

#running the experiment
experimentStartTime = time.time()

subprocess.call(runCommand)

experimentEndTime = time.time()

wallTime = experimentEndTime-experimentStartTime

#updating the memory
memory[ranTheLast]["CumWallTime"] += wallTime
memory[ranTheLast]["#ExperimentsRun"] += 1

with open(memFile,'w') as file:
    json.dump(memory,file)
