#!/usr/bin/env python
"""DeviceRecord.py: a class encapsulating driver for physical devices. Method execute can run as a thread
   for processing requests for the device - project sCribManager - Python."""

'''
@author: Dan Cvrcek, George French
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''
from time import sleep
from threading import Lock
from threading import Thread
from shmLogging import log_trace, log_use

class DeviceRecord(Thread):
    '''
    classdocs
    '''
    def __init__(self, dongle):
        '''
        Constructor
        '''
        try:
            self._dongle = dongle
            self._dongleID = self._dongle.ID()
            self._dongleHWID = self._dongle.HWID()
            self._clusterID = self._dongle.CLUSTER()
        except:
            #ERR125
            log_trace('E', '0052', "Device record constructor error", ID=self._dongleID, HWID=self._dongleHWID, cluster=self._clusterID)
            return None
            
        if (self._dongle.CLUSTER() is None) or (self._dongle.HWID is None) or (self._dongle.ID is None):
            #ERR124
            log_trace('E', '0053', "Hardware malfunction", ID=self._dongleID, HWID=self._dongleHWID, cluster=self._clusterID)
            return None
        
        self._status = 0
        self._new = True
        self._firstCmd = True
        self._errorFlag = False
        self._errorMSg = ""
        self._queue = None
        self._cluster = None
        self._initLock = Lock()

        self._initLock.acquire() # lock the object until a queue is assigned to it
        log_trace('I', '0054', "New device registered", ID=self._dongleID, HWID=self._dongleHWID, cluster=self._clusterID)
        Thread.__init__(self)
    
    def getID(self):
        log_trace('D', '0055', "getID() called", ID=self._dongleID)
        return self._dongleID
    
    def getCluster(self):
        log_trace('D', '0056', "getCluster() called", ID=self._dongleID)
        return self._clusterID
    
    def getHWID(self):
        log_trace('D', '0057', "getHWID() called", ID=self._dongleID)
        return self._dongleHWID
    
    def getStatus(self):
        log_trace('D', '0058', "getStatus() called", ID=self._dongleID)
        return not self._firstCmd
    
    def unplugged(self):
        log_trace('D', '0059', "unplugged() called", ID=self._dongleID)
        return not self._queue
    
    def reopen(self):
        self._dongle.reopen()
    
    def execute(self):
        #wait for the queue to be assigned
        self._initLock.acquire()
        
        self._status = True
        while self._status:
            self._queue['control'].acquire()
            if self._queue['requests'] is None:
                self._cluster['control'].release()
                log_trace('D', '0060', "Queue empty and destroyed", ID=self._dongleID)
                break # we will close, queue is empty and destroyed
            else:
                if (self._queue['length'] > 0) and (self._queue['requests']): # both conditions to check integrity
                    task = self._queue['requests'].pop(0)
                    self._queue['length'] -= 1
                    self._queue['counter'] += 1
                    self._queue['control'].release()
                    # process
                    log_trace('D', '0061', "Request sent to device", ID=self._dongleID, task=task['request'])
                    response = self._dongle.process(task['request'])
                    if response:
                        task['response'] = response
                        log_trace('D', '0062', "request processed by device", ID=self._dongleID, task=task['request'])
                        task['callback'](True, response) # this will free a lock in the TCP server thread
                    else:
                        log_trace('I', '0063', "Request processing failed", ID=self._dongleID, task=task['request'])
                        #device does not respond
                        self._queue['control'].acquire()
                        self._queue['requests'].append(task) #return the task back to the queue
                        self._queue['length'] +=1
                        self._queue['control'].release()
                        self._status = False #we are closing
                        self._queue = None # disassociate from the queue - mark for cancellation
                        task['callback'](False, "ERR114")
                else:

                    if (self._queue['length'] > 0) or (self._queue['requests']): # both conditions to check integrity
                        self._queue['control'].release()
                        log_trace('C', '0064', "Queue integrity test failed", cluster=self._clusterID, ID=self._dongleID, task=task['request'], length=self._queue['length'], requests=self._queue['requests'])
                    else:
                        #the queue is empty, wait 100ms before doing another check
                        self._queue['control'].release()
                        sleep(0.10)
        log_trace('I', '0065', "Device is being removed", ID=self._dongleID, cluster=self._clusterID)
     
 
    def assignQueue(self, queue, cluster):
        self._queue = queue
        self._cluster = cluster
        self._initLock.release()
        log_trace('I', '0066', "Device assigned to a queue", ID=self._dongleID, cluster=self._clusterID, length=queue['length'])


