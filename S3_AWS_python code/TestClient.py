import os
import signal
import subprocess
import logging
import sys
import json
import glob
import time
import re

from stat import ST_MTIME

from flasgger import Swagger
from flask import Flask, jsonify, request, send_file, send_from_directory
from flask_cors import CORS

from ThinClient import ThinClient

thinClient = ThinClient()
# thinClient.initialize(1411572, 2)

LOG_LEVEL = logging.DEBUG
LOG_FORMAT = '%(asctime)s %(module)-20s %(lineno)5d %(levelname)-8s %(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'
LOG_FILENAME = 'agent.log'

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_DATEFMT, filename=LOG_FILENAME)

if LOG_LEVEL == logging.DEBUG:
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

log = logging.getLogger(__name__)
app = Flask(__name__)

app.config['SWAGGER'] = {
    'swagger_version': '2.0',
    'specs': [{
        'version': '0.0.1',
        'title': 'AWS Autotest Client Agent API',
        'endpoint': 'spec',
        'route': '/spec',
        'description': '',
    }]
}

CORS(app)
Swagger(app)
application='powershell'
applicationExe="powershell.exe"
clientLogDir=r'C:\Users\Administrator\Documents\Dylan.dev.Win32'
#clientLogDir=r'C:\Client\Documents\Dylan.dev.Win32'
clientExe='Dylan.Main_Win64_final.exe'


CWD = os.getcwd()
def restoreWorkingDir():
    os.chdir(CWD)

def listFiles(search_dir, file_glob):
    entries = []
    if os.path.exists(search_dir):
        os.chdir(search_dir)
        # remove anything from the list that is not a file (directories, symlinks)
        files = filter(os.path.isfile, glob.glob(file_glob))
        files = [os.path.join(search_dir, f) for f in files] # add path to each file
        files.sort(key=lambda x: os.path.getmtime(x))
        entries = ((file, os.stat(file)[ST_MTIME]) for file in files)
        restoreWorkingDir()
    return entries

def findLatestFile(search_dir, file_glob):
    os.chdir(search_dir)
    # remove anything from the list that is not a file (directories, symlinks)
    files = filter(os.path.isfile, glob.glob(file_glob))
    #files = filter(os.path.isfile, glob.glob("*"))
    #files = filter(os.path.isfile, glob.glob("Runtime*"))
    #files = [os.path.join(search_dir, f) for f in files] # add path to each file
    files.sort(key=lambda x: os.path.getmtime(x))
    restoreWorkingDir()
    return files

@app.route('/api/logfile')
def getLog():
    fromDir = clientLogDir + '\Temp'
    files = findLatestFile(fromDir, 'RunTimeLog*')
    if len(files) > 0:
        filename = files[len(files) -1]
        return send_from_directory(fromDir, filename, as_attachment=True)
    
    resp = {}
    return jsonify(resp)
   
@app.route('/api/logfile/<path:logfile>')
def getLogFile(logfile):
    fromDir = clientLogDir #+ '\Temp'
    filename = os.path.join(clientLogDir, logfile)
    if os.path.isfile(filename):
        return send_from_directory(fromDir, logfile, as_attachment=True)
    
    status = {}
    status['filename'] = filename
    status['status'] = 'file not found'
    resp = jsonify(status)
    resp.status_code = 404
    return resp

def _getLogfileList():
    fromDir=clientLogDir + '\Temp'
    files = listFiles(fromDir, 'RunTimeLog*')
    resp = []
    for file, t in files:
        fileinfo = {}
        fileinfo ['filename'] = os.path.basename(file)
        fileinfo ['timestamp'] = time.ctime(t)
        resp.append(fileinfo)
    return resp

@app.route('/api/logfileList')
def getLogfileList():
    resp = _getLogfileList()    
    return jsonify(resp)

@app.route('/api/crashDump')
def getCrashDump():
    fromDir = clientLogDir + '\CrashDumps'
    files = findLatestFile(fromDir, '*mdmp')
    if len(files) > 0:
        filename = files[len(files) -1]
        return send_from_directory(fromDir, filename, as_attachment=True)
    
    resp = {}
    return jsonify(resp)

@app.route('/api/crashDump/<path:dumpFile>')
def getCrashDumpFile(dumpFile):
    fromDir = clientLogDir #s+ '\CrashDumps'
    filename = os.path.join(clientLogDir, dumpFile)
    if os.path.isfile(filename):
        return send_from_directory(fromDir, dumpFile, as_attachment=True)
    
    status = {}
    status['filename'] = filename
    status['status'] = 'file not found'
    resp = jsonify(status)
    resp.status_code = 404
    return resp

def _getCrashDumpList():
    fromDir = clientLogDir + '\CrashDumps'
    files = listFiles(fromDir, '*mdmp')
    resp = []
    for file, t in files:
        fileinfo = {}
        fileinfo ['filename'] = os.path.basename(file)
        fileinfo ['timestamp'] = time.ctime(t)
        resp.append(fileinfo)

    return resp


@app.route('/api/crashDumpList')
def getCrashDumpList():
    resp = _getCrashDumpList()
    return jsonify(resp)
    
@app.route('/api/clientImage')
def getImage():
    #Check if test is still running.
    status='stopped'
    processList = os.popen('tasklist /fi "imagename eq Dylan.Main_Win64_final.exe"').readlines()
    pidList = []
    for prc in processList:
        tokens=prc.split()
        if len(tokens) > 0:
            if "Dylan.Main_Win64_final.exe" in tokens[0]:
                pidList.append(prc)
                status='running'

    if status == 'running':
        filename = 'clientScreen.jpg'
    else:
        filename = 'clientStopped.jpg'
    if os.path.exists(filename):
        return send_file(filename, mimetype='image/jpeg')
    else:
        status = {}
        status['status'] = 'file not found'
        resp = jsonify(status)
        resp.status_code = 404
        return resp


def getLogFileDataFromFile(logfile, fromDir, gstring):
    data = {}
    outputstr = ''
    filename = os.path.join(fromDir, logfile)
    log.info ("Searching for search string {0}".format(gstring))
    if os.path.isfile(filename):
        file = open( filename, "r")
        for line in file:
            if (gstring == '*'):
                # If jsonify fails due to non utf-8 chars we have to enable following lines
                # Either this: line=line.decode('utf-8','ignore').encode("utf-8") or line=line.decode('iso_8859_1')
                outputstr = outputstr + line
            elif re.search(gstring, line):
                outputstr = outputstr + line
        data['logfile'] = logfile
        # If jsonify fails due to non utf-8 chars we have to either enable above commented line or add following line
        # outputstr = outputstr.decode('utf-8','ignore').encode('utf-8').strip()
        data['logdata'] = outputstr.decode('iso_8859_1')
        resp = jsonify(data)
    else:
        data['logfile'] = 'file not found'
        data['logdata'] = outputstr
        resp = jsonify(data)
        resp.status_code = 404
        
    return resp

@app.route('/api/logfileData')
def getLogFileData():
    gstring = request.args['search']
    log.info ("received search string {0}".format(gstring))
    fromDir = clientLogDir + '\Temp'
    files = findLatestFile(fromDir, 'RunTimeLog*')
    if len(files) > 0:
        logfile = files[len(files) -1]
    else:
        logfile = "RunTimeLog_Empty.log"
        
    resp = getLogFileDataFromFile(logfile, fromDir, gstring)
    
    return resp
    
        
@app.route('/api/logfileData/<logfile>')
def getLogFileDataOfFile(logfile):
    gstring = request.args['search']
    fromDir = clientLogDir + '\Temp'
    log.info ("received search string {0} for logfile {1}".format(gstring,logfile))
    filename = os.path.join(fromDir, logfile)
    filename = logfile
    resp = getLogFileDataFromFile(logfile, fromDir, gstring)
    return resp

@app.route('/api/parselogfile')
def parselogfile():
    resp = {}
    log.info ("received parselogfile")
    fromDir = clientLogDir + '\Temp'
    files = findLatestFile(fromDir, 'RunTimeLog*')
    if len(files) > 0:
        logfile = files[len(files) -1]
    else:
        logfile = "RunTimeLog_Empty.log"
        
    #resp = getLogFileDataFromFile(logfile, fromDir, gstring)
    filename = os.path.join(fromDir, logfile)
    log.info('parsing data {0}'.format(filename))
    clientInfo = os.popen('java -cp C:\ClientLogParser  logparser.LogParser '+filename).readlines()
    if len(clientInfo) > 0:
        log.info('parsed data {0}'.format(clientInfo[0]))
        for prc in clientInfo[0].split(','):
            #log.info('parsed data {0}'.format(prc.strip()))
            prc = prc.replace('{','')
            prc = prc.replace('}','')
            prc = prc.replace('"','')
            #log.info('parsed data after replace {0}'.format(prc.strip()))
            keyValue = prc.split(':',1);
            resp[keyValue[0].strip()] = keyValue[1].strip()
    return jsonify(resp)

@app.route('/api/logs', methods=['DELETE'])
def removeAllLogs():
    #fromDir = clientLogDir + '\Temp'
    #files = findLatestFile(fromDir, 'RunTimeLog*')
    #for file in os.listdir(fromDir):
    #    log.info("Removing log file {0}".format(fromDir+'\\'+file))
    #    os.remove(fromDir+"\\"+file)
    #fromDir = clientLogDir + '\CrashDumps'
    #for file in os.listdir(clientLogDir + '\CrashDumps'):
    #for file in os.listdir(fromDir):
    #    if file.endswith(".mdmp"):
    #        log.info("Removing crash file {0}".format(fromDir+"\\"+file))
    #        os.remove(fromDir+"\\"+file)
    #
    thinClient.removeAllLogs()
    resp = {}
    resp = thinClient.status()
    resp['deleteStatus']='Log And Crash files deleted'
    return jsonify(resp)

@app.route('/api/status', methods=['GET'])
def get_test_status_details():
    resp = {}
    # resp['status']='stopped'
    # processList = os.popen('tasklist /fi "imagename eq Dylan.Main_Win64_final.exe"').readlines()
    # pidList = []
    # for prc in processList:
        # tokens=prc.split()
        # if len(tokens) > 0:
            # if "Dylan.Main_Win64_final" in tokens[0]:
                # pidList.append(prc)
                # resp['status']='running'
    resp = thinClient.status()
    # resp['ProcessList'] = thinClient.
    
    #resp['crashFiles']=_getCrashDumpList()
    #resp['logFiles'] = _getLogfileList()
    try:
        resp['config'] = _getConfig()
    except IOError as e:
        log.error('Failed to read config', e.strerror)
    
    return jsonify(resp)

@app.route('/api/stopClient', methods=['DELETE'])
def StopClientProcess():
    """
    Stop running auto-test client.
    ---
    tags:
      - /api/stopClient
    responses:
      200:
        description: Returns the list of stopped auto-test client PIDs and status.
        schema:
          type: object
          required:
            - status
            - pids
          properties:
            status:
              type: string
            pids:
              type: array
              items:
                type: integer
    """
    resp = {}
    # _StopTestRaceClient()
    thinClient.stopClients()
    resp = thinClient.status()
    #resp['status']='Race Stopped'

    return jsonify(resp)

@app.route('/api/client', methods=['DELETE'])
def StopProcess():
    """
    Stop running auto-test client.
    ---
    tags:
      - /api/client
    responses:
      200:
        description: Returns the list of stopped auto-test client PIDs and status.
        schema:
          type: object
          required:
            - status
            - pids
          properties:
            status:
              type: string
            pids:
              type: array
              items:
                type: integer
    """
    # resp = _StopTest()
    thinClient.stopClients()
    resp = thinClient.status()
    return jsonify(resp)
    
def _StopTest():
    resp = {}
    _StopTestPowershell()
    _StopTestRaceClient()
    pidList = _getRaceClientPidList()
    if len(pidList) == 0:
        resp['status']='Stopped'
    else:
        resp['pids']=pidList
        resp['status']='Still Running'
    return jsonify(resp)
    

def _StopTestPowershell():
    pidList = _getPowershellPidList()
    _killProcess(pidList)
    
def _StopTestRaceClient():
    pidList = _getRaceClientPidList()
    _killProcess(pidList)

def _getPowershellPidList():
    processList = os.popen('tasklist /fi "imagename eq powershell.exe"').readlines()
    pidList = getProcessList("powershell", processList)
    return pidList
    
def _getRaceClientPidList():
    processList = os.popen('tasklist /fi "imagename eq Dylan.Main_Win64_final.*"').readlines()
    pidList = getProcessList("Dylan.Main_Win64_final.", processList)
    return pidList

def getProcessList(processName, processList):
    pidList = []
    for prc in processList:
        tokens=prc.split()
        if len(tokens) > 0:
            if processName in tokens[0]:
                pidList.append(tokens[1])
    return pidList
                
def _killProcess(pidList):
    if len(pidList) >= 1:
        #kill pid and all its child processes
        for pid in pidList:
            os.system('taskkill /f /t /PID '+pid)
    
    
@app.route('/api/client', methods=['GET'])
def get_test_status():
    """
    Get current status of tests.
    ---
    tags:
      - /api/client
    responses:
      200:
        description: Returns the list of PIDs and status.
        schema:
          type: object
          required:
            - status
            - pids
          properties:
            status:
              type: string
            pids:
              type: array
              items:
                type: integer
    """
    resp = {}
    resp['crashFiles']=[]
    resp['status']='stopped'
    processList = os.popen('tasklist /fi "imagename eq Dylan.Main_Win64_final.exe"').readlines()
    pidList = []
	
    for prc in processList:
        tokens=prc.split()
        if len(tokens) > 0:
            if "Dylan.Main_Win64_final.exe" in tokens[0]:
                pidList.append(prc)
                resp['status']='running'
    resp['ProcessList'] = pidList
    
    # check for crash dumps
    crashList=[];
    for file in os.listdir(clientLogDir + '\CrashDumps'):
        if file.endswith(".mdmp"):
            crashList.append(file)
    resp['crashFiles']=crashList
    
    return jsonify(resp)


#start a new process
@app.route('/api/client', methods=['POST'])
def StartProcess():
    """
    Start new auto-test client.
    ---
    tags:
      - /api/client
    parameters:
      - name: Test parameters
        in: body
        schema:
          type: object
          required:
            - Environment
            - Experience
            - Offset
            - Behavior
            - RestartInterval
          properties:
            Environment:
              type: string
              description: loadtest or integration.
            Experience:
              type: string
              description: public or singleplayer.
            Offset:
              type: integer
              description: user instance offset.
            Behavior:
              type: string
              description: public or singleplayer.
            RestartInterval:
              type: integer
              description: public or singleplayer.
            
    responses:
      200:
        description: Returns the list of PIDs and status.
        schema:
          type: object
          required:
            - status
            - pids
          properties:
            status:
              type: string
            pids:
              type: array
              items:
                type: integer
    """
    global thinClient
    params = request.get_json()
    log.info('Received params %s', params)
    clients_per_instance=params.get('num_clients', 2)
    build = params.get('build',1411572)
    start_index = params.get('start_index', 1)
    extraParam = params.get('extraParam', '')
    lindex = params.get('launchIndex', 0)
    print (" Received clients_per_instance = {0}".format(clients_per_instance))
    print (" Received build = {0}".format(build))
    print (" Received extraParam = {0}".format(extraParam))

    instanceRe = re.compile('(.*) -num_clients=(\d*)(.*)')
    match = instanceRe.search(extraParam)
    if (match):
        print ("instanceRe matched extraparam")
        clients_per_instance=int(match.group(2))
        extraParam=match.group(1)+" "+match.group(3)
        print ("Group0 = {0}: Group1 = {1}: Group2 = {2}: Group3 = {3}:".format(match.group(0), match.group(1), match.group(2), match.group(3)))
    
    buildRe = re.compile('(.*) -build=(\d*)(.*)')
    match = buildRe.search(extraParam)
    if (match):
        print ("buildRe matched extraparam")
        build=match.group(2)
        extraParam=match.group(1)+" "+match.group(3)
        print ("Group0 = {0}: Group1 = {1}: Group2 = {2}: Group3 = {3}:".format(match.group(0), match.group(1), match.group(2), match.group(3)))
    
    startIndexRe = re.compile('(.*) -start_index=(\d*)(.*)')
    match = startIndexRe.search(extraParam)
    if (match):
        print ("startIndexRe matched extraparam")
        start_index=int(match.group(2))
        extraParam=match.group(1)+" "+match.group(3)
        print ("Group0 = {0}: Group1 = {1}: Group2 = {2}: Group3 = {3}:".format(match.group(0), match.group(1), match.group(2), match.group(3)))
    
    print ("After RE clients_per_instance ={0}; build={1}; startIndex={2} And extra param ={3}".format( clients_per_instance,  build, start_index, extraParam))
    
    resp = {}

    # Check if test is already running, then stop it 
    thinClient.stopClients()
    
    thinClient.initialize(build, clients_per_instance, start_index, extraParam, lindex)
    thinClient.startClients()
    thinClient.runMonitoring()
    
    resp = thinClient.status()

    return jsonify(resp)


def _getConfig():
    resp = {}
    resp = thinClient.getConfig()
    #resp['experience'] = ""
    #resp['environment'] = ""
    #resp['behavior'] = ""
    #resp['restartInterval'] = ""
    #resp['protocol'] = ""
    #blazeService = params.get('', '')
    #resp['blazeService'] = ""
    #resp['config'] = ""
#    try:
#        with open('testconfig.json') as json_file:
            # data = json.load(json_file)
            # resp = data
            #resp['extraParam'] = data
#            resp['experience'] = data['experience']
#            #resp['environment'] = data['environment']
#            resp['behavior'] = data['behavior']
#            resp['restartInterval'] = data['restartInterval']
#            resp['protocol'] = data['protocol']
#            resp['blazeService'] = data['blazeService']
#            resp['extraParam'] = data['extraParam']
    # except IOError as e:
        # log.error('Failed to read testconfig.json', e.strerror)
    # except Exception as f:
        # log.error('Failed to parse testconfig.json', f)
    return resp


@app.route('/api/config', methods=['GET'])
def getConfig():
    """
    Get current config of test.
    ---
    tags:
      - /api/config
    responses:
      200:
        description: Returns the list of PIDs and status.
        schema:
          type: object
          required:
            - experience
            - behavior
            - environment
            - protocol
            - restartInterval
          properties:
            status:
              type: string
            pids:
              type: array
              items:
                type: integer
    """
    resp = _getConfig()
    return jsonify(resp)

#Modify the config parameters
@app.route('/api/config', methods=['POST'])
def updateConfig():
    """
    Start new auto-test client.
    ---
    tags:
      - /api/config
    parameters:
      - name: Test parameters
        in: body
        schema:
          type: object
          required:
            - Environment
            - Experience
            - Offset
            - Behavior
            - RestartInterval
          properties:
            Environment:
              type: string
              description: loadtest or integration.
            Experience:
              type: string
              description: public or singleplayer.
            Offset:
              type: integer
              description: user instance offset.
            Behavior:
              type: string
              description: public or singleplayer.
            RestartInterval:
              type: integer
              description: public or singleplayer.
            
    responses:
      200:
        description: updates config.
        schema:
          type: object
          required:
            - status
            - pids
          properties:
            status:
              type: string
            pids:
              type: array
              items:
                type: integer
    """
    params = request.get_json()
    log.info('Received params %s', params)
    clients_per_instance=params.get('clients_per_instance', 1)
    experience = params.get('Experience', 'public')
    #environment = params.get('Environment', 'loadtest')
    behavior = params.get('Behavior', 'restartOnExit')
    restartInterval = int(params.get('RestartInterval',-1))
    protocolString = params.get('Protocol',"")
    blazeService = params.get('blazeService', 'nfs-2018-pc-stress')
    extraParam = params.get('extraParam', '')
    
    resp = {}

    try:
        with open('testconfig.json') as json_file:
            data = json.load(json_file)
            data['experience'] = experience
            #data['environment'] = environment
            data['behavior'] = behavior
            data['restartInterval'] = restartInterval
            data['protocol'] = protocolString
            data['blazeService'] = blazeService
            data['extraParam'] = extraParam
        
        with open('testconfig.json', 'w') as outfile:
            json.dump(data, outfile)
        resp['result']='config updated'
    except IOError as e:
        log.error('Failed to read testconfig.json', e.strerror)
        resp['result']='failed to update config'
    
    return jsonify(resp)
    

# Take log and crash backup
@app.route('/api/crashlog', methods=['Get'])
def backupLog():
    """
    Start new auto-test client.
    ---
    tags:
      - /api/crashlog
    parameters:
      - name: Test parameters
        in: body
        schema:
          type: object
          required:
            - Environment
            - Experience
            - Offset
            - Behavior
            - RestartInterval
          properties:
            Environment:
              type: string
              description: loadtest or integration.
            Experience:
              type: string
              description: public or singleplayer.
            Offset:
              type: integer
              description: user instance offset.
            Behavior:
              type: string
              description: public or singleplayer.
            RestartInterval:
              type: integer
              description: public or singleplayer.
            
    responses:
      200:
        description: updates config.
        schema:
          type: object
          required:
            - status
            - pids
          properties:
            status:
              type: string
            pids:
              type: array
              items:
                type: integer
    """
    params = request.get_json()
    log.info('Received params %s', params)    
    resp = {}

    resp['status']='backup done'
    return jsonify(resp)    


##### To run it as flask service execute the following    
#export FLASK_APP=C:\bin\TestClient.py
#flask run --host=0.0.0.0 

if __name__ == '__main__':
    app.run(host='0.0.0.0',threaded=True,debug=True)