import subprocess
import requests
import os
import time
import threading
from subprocess import Popen, PIPE
import shutil
import socket
import datetime
from stat import ST_MTIME
import json
#print("Syncing....")

class ThinClient(object):
    def __init__(self):
        ###################### Global Variables ##########
        self.amazonUserDataUrl = 'http://169.254.169.254/latest/user-data/'
        self.ami_launch_index_url = 'http://169.254.169.254/latest/meta-data/ami-launch-index' #ami-launch-index
        #self.base_path=r'C:\Client'
        self.base_path=r'C:\Users\Administrator'
        #self.clientLogDir=r'C:\Users\Administrator\Documents\Dylan.dev.Win32'
        self.clientLogDir=self.base_path + '\Documents\Dylan.dev.Win32'
        self.basePort = 3216
        self.processArray = []
        self.logfile = open("thinclient_log.txt","w") 
        self.userNames = []
        self.monitor = False
        self.monitorClientProcessing = False
        self.monitorThreadStarted = False
        self.configfile = "testconfig.json"
        #try:
            #self.launch_index = requests.get(url = self.ami_launch_index_url)
            #self.lindex = self.launch_index.json()
        #except Exception as e:
        #    self.lindex = 0
        self.lindex = 0
        self.extraParams = ""
        print("launch index : ", self.lindex) 
        self.index = 1
        self.start_index = 1
        self.build  = 1433682
        self.instanceCount = 1
        
        try:
            if os.path.exists(self.configfile):
                with open(self.configfile) as json_file:
                    data = json.load(json_file)
                    self.lindex = int(data['launch_index'])
                    self.start_index = int(data['start_index'])
                    self.instanceCount = int(data['instanceCount'])
                    self.build = int(data['build'])
                    self.extraParams = data['extraParams']
                    userNames = data['userNames']
                    for user in userNames:
                        self.userNames.append(user)
        except IOError as e:
            print ('Failed to read testconfig.json', e.strerror)
        except Exception as f:
            print ('Failed to parse testconfig.json', f)
        
        ###################################################

    def initialize(self, lbuild, instanceCnt, startIndex, otherParam,launchIndex):
        #global index, userNames
        self.build = lbuild
        self.instanceCount = instanceCnt
        self.start_index = startIndex
        self.extraParams = otherParam  
        self.lindex = launchIndex
        #userData = requests.get(url = amazonUserDataUrl)
        #self.data = userData.json()
        #self.start_index = data['startIndex']
        #self.instanceCount = data['instanceCount']
        #self.build = data['build']
        print ("Received build={0}; instanceCnt={1}; startIndex={2}; others={3}; AMI-launchIndex = {4}".format(self.build, self.instanceCount, self.start_index, self.extraParams, self.lindex))

        #path = 'C:/Users/Administrator/Build/'+str(self.build)
        path = self.base_path + '/Build/GameBuilds/'+str(self.build)
        Deletepath = self.base_path + '/Build/GameBuilds/'
        if os.path.exists(path):
            print("Build directory exists")
        else:
            if os.path.exists(Deletepath):
                self.logfile.write("Delete old builds if any at path {0}".format(Deletepath))
                shutil.rmtree(Deletepath)
            self.logfile.write("Donwload started to path {0}".format(path))
            print ("Donwload started to path {0}".format(path))
            subprocess.call(['aws', 's3', 'sync','s3://ea-anthem-game-client-systest/Builds/'+str(self.build),path])
            self.logfile.write("Donwload completed")
            print ("Donwload completed")

        self.userNames = []
        self.index = 1
        self.index = self.start_index + self.lindex * self.instanceCount
        print ("instanceCount {0}; lindex{1}; index  {2}".format(self.instanceCount, self.lindex, self.index))
        #usernames = ['anthemgs0000@gos.ea.com','anthemgst0499@gos.ea.com']
        for i in range(self.instanceCount):
            user = 'anthemgs' + str(self.index).zfill(4) + '@gos.ea.com'
            self.userNames.append(user)
            self.index = self.index + 1
        

        #file = open("testconfig.json","w") 
        with open(self.configfile,'w') as file:
            file.write("{\"launch_index\" : \"%s\",\n" % str(self.lindex))
            file.write("\"start_index\" : \"%s\",\n" % str(self.start_index))
            file.write("\"instanceCount\" : \"%s\",\n" % str(self.instanceCount))
            file.write("\"build\" : \"%s\",\n" % str(self.build))
            file.write("\"extraParams\" : \"%s\",\n" % str(self.extraParams))
            file.write("\"userNames\" : [ " )
            firstName=True
            for user in self.userNames:
                if (firstName == True):
                    file.write("\n\"%s\""%user)
                    firstName = False
                else:
                    file.write(",\n\"%s\""%user)
            file.write("\n]}" )
            file.close()

        self.monitorClients()

    def startClients(self):
        i = 0
        exe = self.base_path + '/Build/GameBuilds/'+ str(self.build)+'/Dylan.Main_Win64_final.exe'
        #for user in self.userNames :
            #port = self.basePort + i*4;
            #print ("Starting Origin for user {0} on port {1}".format(user, port))
            #subprocess.call('"C:\Program Files (x86)\Origin Launcher\OriginLauncher.exe" -Origin_MultipleInstances -username:'+user+' -password:Loadtest1234 -LsxPort:'+str(port)+' -start ')
            #print ("Started Origin process")
            #i = i+1
            #time.sleep(15)
        #i = 0
        #time.sleep(20)
        for user in self.userNames :
            # port = self.basePort + i*4;
            # #op = subprocess.Popen('"C:\Program Files (x86)\Origin Launcher\OriginLauncher.exe" -Origin_MultipleInstances -username:'+user+' -password:Loadtest1234 -LsxPort:'+str(port)+' -start ')
            # orin = ['-Origin.LsxPort']
            # orin.append(str(port))
            # # Separate Log dir for each instance of running client ex: ThinClient0\Temp
            # clientPath = self.clientLogDir + '\ThinClient'+str(i)
            # orin.append('-Client.InstancePath')
            # orin.append(clientPath)
            # extraParam = self.extraParams.strip()
            # if not extraParam:
                # orin.append(extraParam)
            # self.backupLogFile(clientPath+"\Temp")
            time.sleep(40)
            #path = self.base_path + '/Build/GameBuilds/'+str(self.build)
            #exe = str(self.build)+'\Dylan.Main_Win64_final.exe'
            #print ("Starting GameClient for user {0} on port {1}, {2}, {3}".format(user, port, exe, [exe]+orin))
            # p = subprocess.Popen([exe]+orin,stdout=PIPE)
            p = self.startClientProcess(exe, i)
            self.processArray.append(p)
            print ("Started process PID is {0}".format(p.pid))
            i = i+1

    def startClientProcess(self, exe, i):
        port = self.basePort + i*4
        orin = ['-Origin.LsxPort']
        orin.append(str(port))
        # Separate Log dir for each instance of running client 
        clientPath = self.clientLogDir + '\ThinClient'+str(i)
        orin.append('-Client.InstancePath')
        orin.append(clientPath)
        extraParam = self.extraParams.strip()
        if not extraParam:
            orin.append(extraParam)
        self.backupLogFile(clientPath+"\Temp")
        p = subprocess.Popen([exe]+orin,stdout=PIPE)
        return p
        
    def backupLogFile(self, logdir):
        # Following are alternatives for getting hostname
        # >>> import platform
        # >>> import socket
        # >>> import os
        # >>> platform.node()
        # 'EC2AMAZ-5TP81VH'
        # >>> socket.gethostname()
        # 'EC2AMAZ-5TP81VH'
        # >>> os.environ['COMPUTERNAME']
        # 'EC2AMAZ-5TP81VH'
        computername = socket.gethostname()
        logfile = logdir + "\RuntimeLog_" + computername + ".log" # Ex: EC2AMAZ-5TP81VH.log"
        if os.path.exists(logfile):
            # get the latest file and rename it with timestamp
            dt = str(datetime.datetime.now())
            logfileBackup = logdir + "\RuntimeLog_" + computername + '_' + "{0}".format(time.strftime("%Y%m%d%H%M%S")) + '.log'
            print ("Taking backup of file {0} as {1} ".format(logfile, logfileBackup))
            os.rename(logfile, logfileBackup)
    
    def runMonitoring(self):
        self.monitor = True
        self.monitorClients()

    def stopMonitoring(self):
        self.monitor = False
        
    def monitorClients(self):
        #if (self.monitor == True):
        if (self.monitorThreadStarted == False):
            self.monitoringThread = threading.Thread(target=self.monitorClientsThread)
            self.monitoringThread.start()
            self.monitorThreadStarted = True
        else:
            if (self.monitoringThread.isAlive() == False):
                self.monitoringThread = threading.Thread(target=monitorClientsThread)
                self.monitoringThread.start()

    def monitorClientsThread(self):
        # to restart all crashed clients
        while (True) :
            exe = self.base_path + '/Build/GameBuilds/'+ str(self.build)+'\Dylan.Main_Win64_final.exe'
            time.sleep(60)
            if (self.monitor == True):
                self.monitorClientProcessing = True
                i = 0
                print("processArray size is :",len(self.processArray))
                for p in self.processArray:
                    if p.poll():
                        self.processArray.remove(p)
                        # port = self.basePort + i*4
                        # orin = ['-Origin.LsxPort']
                        # orin.append(str(port))
                        # # Separate Log dir for each instance of running client 
                        # clientPath = self.clientLogDir + '\ThinClient'+str(i)
                        # orin.append('-Client.InstancePath')
                        # orin.append(clientPath)
                        # extraParam = self.extraParams.strip()
                        # if not extraParam:
                            # orin.append(extraParam)
                        # self.backupLogFile(clientPath+"\Temp")
                        #print("crashed : {0}, restarting on port {1}".format(i, port))
                        # #exe = str(self.build)+'\Dylan.Main_Win64_final.exe'
                        # p = subprocess.Popen([exe]+orin,stdout=PIPE)
                        p = self.startClientProcess(exe, i)
                        self.processArray.insert(i,p)
                        print("     Restarted Crashed: {0}, Pid {1}".format(i, p.pid))
                        time.sleep(35)
                    i = i+1
                self.monitorClientProcessing = False

    def status(self):
        resp = {}
        while(self.monitorClientProcessing == True):
            # Wait for monitor thread to complete its loop
            time.sleep(1)
        pidList = self.getPidList("Dylan.Main_Win64_final")
        resp['ProcessList'] = pidList
        resp['totalProcess'] = self.instanceCount
        if ( len(pidList) == 0):
           resp['status'] = 'stopped'
        elif (len(pidList) == self.instanceCount):
           resp['status'] = 'running'
        else:
           resp['status'] = 'impaired'
        # check for crash dumps
        crashList=self.getCrashList()   #[];
        #if os.path.exists(self.clientLogDir + '\CrashDumps'):
        #    for file in os.listdir(self.clientLogDir + '\CrashDumps'):
        #        if file.endswith(".mdmp"):
        #            crashList.append(file)
        resp['crashFiles']=crashList
        
        logfilelist = self.getLogFileList()
        resp['logFiles'] = logfilelist
        
        try:
            resp['config'] = self.getConfig()
        except IOError as e:
            log.error('Failed to read config', e.strerror)
            
        print (resp)
        return resp
    
    def getConfig(self):
        resp = ""
        try:
            with open(self.configfile) as json_file:
                data = json.load(json_file)
                configData = " -num_clients={0} -build={1} -start_index={2} {3}".format(data['instanceCount'], data['build'], data['start_index'], self.extraParams.strip())
                resp = configData
        except IOError as e:
            log.error('Failed to read testconfig.json', e.strerror)
        except Exception as f:
            log.error('Failed to parse testconfig.json', f)
        return resp
    
    def getCrashList(self):
        i=0
        crashList=[]
        #for p in self.processArray:
        for p in range(self.instanceCount):
            crashdumpPath = self.clientLogDir + '\ThinClient'+str(i) + '\CrashDumps'
            if os.path.exists(crashdumpPath):
                for file in os.listdir(crashdumpPath):
                    if file.endswith(".mdmp"):
                        filedata = {}
                        filedata['filename'] = os.path.join('ThinClient'+str(i) + '\CrashDumps' , file)
                        filedata['timestamp'] = time.ctime(os.stat(os.path.join(crashdumpPath , file))[ST_MTIME])
                        crashList.append(filedata)
            i = i+1
        return crashList
    
    def getLogFileList(self):
        i=0
        logfileList=[]
        #for p in self.processArray:
        for p in range(self.instanceCount):
            logfilePath = self.clientLogDir + '\ThinClient'+str(i) + '\Temp'
            print ("Looking in dir {0}".format(logfilePath))
            if os.path.exists(logfilePath):
                for file in os.listdir(logfilePath):
                    if file.endswith(".log"):
                        filedata = {}
                        filedata['filename'] = os.path.join('ThinClient'+str(i) + '\Temp' , file)
                        filedata['timestamp'] = time.ctime(os.stat(os.path.join(logfilePath , file))[ST_MTIME])
                        logfileList.append(filedata)
            i = i+1
        return logfileList
    
    def removeAllLogs(self):
        i=0
        for p in range(self.instanceCount):
            logfilePath = self.clientLogDir + '\ThinClient'+str(i) + '\Temp'
            print ("Cleaning dir {0}".format(logfilePath))
            if os.path.exists(logfilePath):
                for file in os.listdir(logfilePath):
                    if file.endswith(".log"):
                        os.remove(os.path.join(logfilePath , file))
            crashdumpPath = self.clientLogDir + '\ThinClient'+str(i) + '\CrashDumps'
            print ("Cleaning dir {0}".format(crashdumpPath))
            if os.path.exists(crashdumpPath):
                for file in os.listdir(crashdumpPath):
                    if file.endswith(".mdmp"):
                        os.remove(os.path.join(crashdumpPath , file))
            i = i+1
    
    def stopClients(self):
        # to stop all running clients first disable monitoringThread
        self.stopMonitoring()
        while(self.monitorClientProcessing == True):
            # Wait for monitor thread to complete its loop
            time.sleep(1)
        i = 0
        self.stopProcesses("Dylan.Main_Win64_final")
        self.processArray=[]
        #self.stopProcesses("Origin")
        
        
    def stopProcesses(self, process):
        pidList = self.getPidList(process)
        if len(pidList) >= 1:
            #kill pid and all its child processes
            for pid in pidList:
                print ("Killing Pid {0}".format(pid))
                os.system('taskkill /f /t /PID '+pid)
    #
    def getPidList(self, process):
        #processList = os.popen('tasklist /fi "imagename eq Dylan.Main_Win64_final.*"').readlines()
        #pidList = self.getProcessList("Dylan.Main_Win64_final.", processList)
        processList = os.popen('tasklist /fi "imagename eq ' + process + '.*"').readlines()
        pidList = self.getProcessList(process+".", processList)
        return pidList

    def getProcessList(self, processName, processList):
        pidList = []
        for prc in processList:
            tokens=prc.split()
            if len(tokens) > 0:
                if processName in tokens[0]:
                    pidList.append(tokens[1])
        return pidList       
#

# thinClient = ThinClient()
# thinClient.initialize(1411572, 2)
# thinClient.startClients()
# thinClient.runMonitoring()
# time.sleep(30)
# thinClient.stopClients()
