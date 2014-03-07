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
        self.janitor = Thread(target=self.janitorClass.run)
        #self.janitor.daemon = True
        self.janitor.start()
        

    
    def _parseRequest(self, requestString):
        request = requestString.split()
        if request[0] in self._commands:
            return True
        elif request[0] in self._clustercommands:
            return True
        else:
            return False
        
    
    def getRequestCluster(self, requestString):
        request = requestString.split()
        if (self.isClusterRequest(requestString)):
            request[0] = self._clustercommands[request[0]]
        else:
            request[0] = self._commands[request[0]]
        if len(request)>1:
            cluster = request.pop(1)
            return (cluster, ' '.join(request))
        else:
            return (None, request[0])
    
    
    def isClusterRequest(self, request):
        parts = request.split()
        try:
            if parts[0] in self._clustercommands:
                return True
            elif int(parts[0])>100:
                return True
            else:
                return False
        except:
            return False
    
    def newRequest(self, requestString, callback_function):
        ''' 
        Simple add to a queue for the given cluster
        '''
        print("QueueManager - New request received %s"%requestString)
        if not self._running:
            return False
        
        # test we are still running
        if not self._shuttingDown:
            
            if self._parseRequest(requestString):
                (clusterID, request) = self.getRequestCluster(requestString)
                if clusterID is None:
                    print ("The API key is incorrect - request %s" % requestString)
                    callback_function(False, "ERR207")
                    return False
                else:
                    if (self.isClusterRequest(request)):
                        response = self.process(clusterID, request)
                        callback_function(True, response)
                        return True
                    else:
                        if clusterID in self._Queues.keys():
                            self._Queues[clusterID]['control'].acquire()
                            if (not self._Queues[clusterID]['requests']):
                                self._Queues[clusterID]['requests'] = []
                            self._Queues[clusterID]['requests'].append({'request': request, 'callback': callback_function, 'timein':time.time()})
                            self._Queues[clusterID]['length'] += 1
                            self._Queues[clusterID]['control'].release()
                            return True
                        else:
                            print("No Hardware for the cluster %s" % clusterID )
                            callback_function(False, "ERR115")
                            return False
                    # end of if ... else
            else:
                print("The command has not been recognised %s" % requestString.strip())
                callback_function(False, "ERR116")
                return False
        else:
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
                data = "ERR127"
        except:
            data = "ERR128"
                     
        return data

        
    def GETCLUSTERCOUNTER(self, cluster):
        if cluster in self._Queues:
            counter = self._Queues[cluster]['counter']
            return "%0.8X" % counter
        else:
            return "ERR207"
    
    def GETCLUSTERDONGLES(self, cluster):
        if cluster in self._Queues:
            devices = self.janitorClass.getDevices(cluster)
            return " ".join(devices)
        else:
            return "ERR207"
    
    def GETCLUSTERID(self, cluster):
        if cluster in self._Queues:
            return cluster
        else:
            return "ERR207"
    
    def GETCLUSTERLOCKED(self, cluster):
        return "ERR129"
    
    def GETCLUSTERDELAY(self, cluster):
        return "ERR129"
    
    def processing(self):
        '''
        This will start serving
        '''
        self._watch = Thread(target=self.queueWatch)
        #self.janitor.daemon = True
        self._watch.start()
        self._running = True
        
        
        '''
        at the end - just call the callback function with the result
        '''
        
        
    def shutdown(self):
        '''
        set the flag to signal no more requests
        '''
        self._shuttingDown = True
        '''
        Wait for all requests to be processed
        '''
        return True
        
        
    def shutdownHard(self):
        self._shuttingDown = True
        self._shuttingNow = True
