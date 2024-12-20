import os
import time #for Runtime
import tracemalloc #for memory usage


#An object that takes a python method as input and measures its memory consumption and runtime. 
#The output will be written to a csv file. The method can return additional infos as dict, which will be logged along side the performance data.
class profiler:

    def __init__(self,taskToProfile,resultFile):
        self.task = taskToProfile
        self.resultFile = resultFile

    def _saveResult(self):
        
        #Create Dirs if not existent
        if "/" in self.resultFile:
            fileNameLength = len(self.resultFile.split("/")[-1])
            folders = self.resultFile[:-fileNameLength]
            os.makedirs(folders,exist_ok=True)

        #Create File if not existent
        if not os.path.exists(self.resultFile):
            resultHead = ""
            for key in self.data:
                resultHead+= key+","
            resultHead = resultHead[:-1]+"\n"
            with open(self.resultFile,'w') as f:
                f.write(resultHead)
        
        #Write Rundata to file
        line = ""
        for key in self.data:
            line += str(self.data[key])+','
        line = line[:-1]+"\n"
        with open(self.resultFile,'a') as f:
            f.write(line)

    def measure(self):

        runData = {
                "Memory/KiB":float("NaN"),
                "Memory Peak/KiB":float("NaN"),
                "Process Runtime/s":float("NaN"),
                "Time Elapsed/s":float("NaN"),
                }

        tracemalloc.start()
        process_start = time.process_time()
        start = time.time()
        ## Experiment Here
        ############################

        additionalData = self.task()

        #############################
        ##
        process_end = time.process_time()
        end = time.time()
        
        runData["Memory/KiB"],runData["Memory Peak/KiB"] = tracemalloc.get_traced_memory()
        runData["Process Runtime/s"] = process_end-process_start
        runData["Time Elapsed/s"] = end - start
        tracemalloc.stop()

        runData.update(additionalData)
        self.data = runData

        self._saveResult()
