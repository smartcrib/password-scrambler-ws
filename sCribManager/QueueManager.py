#!/usr/bin/env python

"""QueueManager.py: a class accepts requests from InternalTCPServer and facilitates their processing by hardware devices:
   project S-CribManager - Python."""

'''
@author: Dan Cvrcek, George French
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''
from shmLogging import log_trace, log_use
from DeviceJanitor import DeviceJanitor
from threading import Thread
import time

class QueueManager(Thread):
    '''
    This class will receive requests from Handler instances, processes them and returns results
    to callback methods 
    '''
    _TASK_TIMEOUT = 5 #requests must be processed within some seconds
    
    _commands = {
                 'GETINITKEY':'2',
                 'GETPASSWD':'3',
                 'GETID':'4',
                 'ENGETID':'5',
                 'GETCOUNTER':'6',
                 'GETDELAY':'7',
                 'GETCLUSTER':'8',
                 'GETLOCKED':'9',
                 'SCRAMBLE':'10',
                 'ENSCRAMBLE':'11',
                 }

    _clustercommands = {
                 'GETCLUSTERCOUNTER':'101',
                 'GETCLUSTERDONGLES':'102',
                 'GETCLUSTERID':'103',
                 'GETCLUSTERLOCKED':'104',
		 'GETCLUSTERDELAY':'105',
                 }
   
    _apicommands = {
                 'ADDAPICLIENT':'201',
                 'CHECKAPICLIENT':'202',
                 }
    
    def __init__(self):
        '''
        Constructor
        '''
        
        ''' create thread for checking status of hardware
        '''
            
        self._Queues = {}
        self._running = False
        self._shuttingDown = False
        self._shuttingNow = False   # this means- no more processing, just finish current request
        self._watch = None
        self.janitorClass = DeviceJanitor(self._Queues)
        log_trace('I', '0036', "Janitor created", detail="n/a")
        self.janitor = Thread(target=self.janitorClass.run)
        #self.janitor.daemon = True
        self.janitor.start()
        log_trace('I','0037', "Janitor started", detail="n/a") 

    
    def _parseRequest(self, requestString):
        request = requestString.split()
        if request[0] in self._commands:
            return True
        elif request[0] in self._clustercommands:
            return True
        elif request[0] in self._apicommands:
            return True
        else:
            return False
        
    
    def getRequestCluster(self, requestString):
        cluster = None

        request = requestString.split()
        if self.isClusterRequest(requestString):
            request[0] = self._clustercommands[request[0]]
        elif self.isAPIRequest(requestString):
            request[0] = self._apicommands[request[0]]
	    cluster = "virtual"
        else:
            request[0] = self._commands[request[0]]

        if (len(request)>1) and (cluster is None):
            cluster = request.pop(1)
            return(cluster, ' '.join(request))
        elif cluster is None:
            return(None, request)  #error 
        else:
            return(cluster, ' '.join(request)) #API command

    def isClusterRequest(self, request):
        parts = request.split()
        try:
            if parts[0] in self._clustercommands:
                return True
            elif (int(parts[0])>100) and (int(parts[0])<200):
                return True
            else:
                return False
        except:
            return False
   
    def isAPIRequest(self, request):
        parts = request.split()
	if len(parts)<2:
            return False #the command must be at least one param - API key
        try:
            if parts[0] in self._apicommands:
                return True
            elif (int(parts[0])>200) and(int(parts[0])<300):
                return True
            else:
                return False
        except:
            return False

    def newRequest(self, requestString, callback_function):
        ''' 
        Simple add to a queue for the given cluster
        '''
        log_trace("D",'0017', "QueueManager received request", detail=requestString)
        if not self._running:
            log_trace("C", '0018', "QueueManager not running", command=requestString)
            return False
        
        # test we are still running
        if not self._shuttingDown:
            
            if self._parseRequest(requestString):
                (clusterID, request) = self.getRequestCluster(requestString)
                if clusterID is None:
                    log_trace("I", '0020', "Request with incorrect clusterID", command=requestString, err="ERR207")
                    callback_function(False, "ERR207")
                    return False
                else:
                    if (self.isClusterRequest(request)):
                        log_trace("D", '0021', "Received cluster request", detail=requestString)
                        response = self.process(clusterID, request)
                        callback_function(True, response)
                        return True
                    elif (self.isAPIRequest(request)):
                        log_trace('D', '0022', "Received API request", detail=requestString)
                        params = request.split(' ',1)
			command = params[0].strip()
			callback_function(True, "ERR211 "+command+" "+params[1].strip())
                        return True
                    else:
                        log_trace('D', '0023', "Received user request", cluster=clusterID)
                        if clusterID in self._Queues.keys():
                            self._Queues[clusterID]['control'].acquire()
                            if (not self._Queues[clusterID]['requests']):
                                self._Queues[clusterID]['requests'] = []
                            self._Queues[clusterID]['requests'].append({'request': request, 'callback': callback_function, 'timein':time.time()})
                            self._Queues[clusterID]['length'] += 1
                            self._Queues[clusterID]['control'].release()
                            return True
                        else:
                            log_use('0006', "No HW available", cluster =clusterID)
                            callback_function(False, "ERR115")
                            return False
                    # end of if ... else
            else:
                log_trace('I', '0024', "Unknown command received", command=requestString)
                callback_function(False, "ERR116")
                return False
        else:
            log_trace('I', '0025', "Command received when QueueManager is being shut down", command=requestString)
            callback_function(False, "ERR117") # the system is being shutdown
            return False
        
    def queueWatch(self):   
        # here we can do some health checks over queues 
        while not self._shuttingNow:
            timestamp = time.time()
            totalTasks = 0
            for clusterID in self._Queues:
                queue = self._Queues[clusterID]
                queue['control'].acquire()
                tasksToClear = []
                totalTasks += len(queue['requests'])
                for taskIdx in range(len(queue['requests'])):
                    if (timestamp - queue['requests'][taskIdx]['timein'])>self._TASK_TIMEOUT:
                        tasksToClear.append(taskIdx)
                while tasksToClear:
                    taskIdx = tasksToClear.pop()
                    log_use('0007', "Request timed out", timeout=self._TASK_TIMEOUT, command=taskIdx['request'])
                    queue['requests'][taskIdx]['callback'](False, "ERR126")
                    del queue['requests'][taskIdx]
                    queue['length'] -= 1
                queue['control'].release()
            if self._shuttingDown and totalTasks == 0:
                self._shuttingNow = True
            time.sleep(5)
        # close now
        for clusterID in self._Queues:
            queue = self._Queues[clusterID]
            queue['control'].acquire()
            tasksToClear = []
            totalTasks += len(queue['requests'])
            while queue['requests']:
                del queue['requests'][0]
                queue['length'] -= 1
            queue['control'].release()
        pass
        
    def process(self, cluster, request):
        
        request_bits = request.split()
        command = int(request_bits[0])
        t_start = time.time()
        try:
            if command == 101: #'GETCLUSTERCOUNTER':'101',
                data = self.GETCLUSTERCOUNTER(cluster)
            elif command == 102: #'GETCLUSTERDONGLES':'102',
                data = self.GETCLUSTERDONGLES(cluster)
            elif command == 103: #'GETCLUSTERID':'103',
                data = self.GETCLUSTERID(cluster)
            elif command == 104: #'GETCLUSTERLOCKED':'104',
                data = self.GETCLUSTERLOCKED(cluster)
            elif command == 105: #'GETCLUSTERDELAY':'105',
                data = self.GETCLUSTERDELAY(cluster)
            else:
                log_trace('I', '0027', "Unknown cluster command", command=requestString)
                data = "ERR127"
        except:
            log_trace('E', '0026', "Exception while processing cluster command", command=requestString)
            data = "ERR128"
        latency = time.time() - t_start
        log_use('0008', "Cluster command processed", command=request, time=latency)

        return data

    def GETCLUSTERCOUNTER(self, cluster):
        if cluster in self._Queues:
            counter = self._Queues[cluster]['counter']
            return "%0.8X" % counter
        else:
            log_trace('D', '0028', "Unknown cluster - GETCLUSTERCOUNTER", cluster=cluster)
            return "ERR207"
    
    def GETCLUSTERDONGLES(self, cluster):
        if cluster in self._Queues:
            devices = self.janitorClass.getDevices(cluster)
            return " ".join(devices)
        else:
            log_trace('D', '0029', "Unknown cluster - GETCLUSTERDONGLES", cluster=cluster)
            return "ERR207"
    
    def GETCLUSTERID(self, cluster):
        if cluster in self._Queues:
            return cluster
        else:	
            log_trace('D', '0030', "Unknown cluster - GETCLUSTERID", cluster=cluster)
            return "ERR207"
    
    def GETCLUSTERLOCKED(self, cluster):
        return "ERR129"
    
    def GETCLUSTERDELAY(self, cluster):
        return "ERR129"
   
    '''
    This method simply starts a new thread - queueWatch so that request can be served.
    ''' 
    def processing(self):
        '''
        This will start serving
        '''
        self._watch = Thread(target=self.queueWatch)
        #self.janitor.daemon = True
        self._watch.start()
        self._running = True
        log_trace('I', '0031', "Processing - queueWatch started", detail="n/a")
        '''
        at the end - just call the callback function with the result
        '''
        
        
    '''
    Initiate shutdown - stop accepting requests from clients.
    '''
    def shutdown(self):
        '''
        set the flag to signal no more requests
        '''
        self._shuttingDown = True
        '''
        Wait for all requests to be processed
        '''
        log_trace('I', '0032', "System is shutting down - no more requests accepted", detail="n/a")
        return True
        
        
    '''
    Initiate hard shutdown - stop accepting requests from clients and remove all
    requests waiting in queues.
    '''
    def shutdownHard(self):
        self._shuttingDown = True
        self._shuttingNow = True
        log_trace('I', '0033', "System is shutting down hard - no more requests & purge queues", detail="n/a")

