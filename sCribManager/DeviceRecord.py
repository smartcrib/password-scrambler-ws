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
            print("Creating DeviceRecord with invalid dongle class")
            return None
            
        if (self._dongle.CLUSTER() is None) or (self._dongle.HWID is None) or (self._dongle.ID is None):
            #ERR124
            print("Creating DeviceRecord with non-functional hardware dongle - unplugged: %s %s %s"%(self._dongleID, self._dongleHWID, self._clusterID))
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
        print("A device %s (HW ID: %s) created - cluster %s"%(self._dongleID, self._dongleHWID, self._clusterID)) 
        Thread.__init__(self)
    
    def getID(self):
        return self._dongleID
    
    def getCluster(self):
        return self._clusterID
    
    def getHWID(self):
        return self._dongleHWID
    
    def getStatus(self):
        return not self._firstCmd
    
    def remove(self):
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
                break # we will close, queue is empty and destroyed
            else:
                if (self._queue['length'] > 0) and (self._queue['requests']): # both conditions to check integrity
                    task = self._queue['requests'].pop(0)
                    self._queue['length'] -= 1
                    self._queue['counter'] += 1
                    self._queue['control'].release()
                    # process
                    
                    print("Request %s to be sent to device %s" %(task['request'], self._dongleID))
                    response = self._dongle.process(task['request'])
                    if response:
                        task['response'] = response
                        print("Request %s processed by device %s" % (task['request'], self._dongleID))

                        task['callback'](True, response) # this will free a lock in the TCP server thread
                    else:
                        print("Request %s failed by device %s" % (task['request'], self._dongleID))
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
                        raise ValueError('Integrity error in cluster %s'%self._clusterID)
                    else:
                        self._queue['control'].release()
                        sleep(0.10)
        print("A device %s is exiting" % self._dongleID)
      
    def assignQueue(self, queue, cluster):
        self._queue = queue
        self._cluster = cluster
        self._initLock.release()
        print("A queue assigned to device %s (length is %d)" %(self.getID(), queue['length']))


        
