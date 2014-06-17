#!/usr/bin/env python

"""DeviceJanitor.py: a process that checks status of hardware devices and updates their status sCribManager - Python."""

'''
@author: Dan Cvrcek, George French
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''

import time
import sys
from threading import Thread
from shmLogging import log_trace, log_use
from DeviceRecord import DeviceRecord
from sCribDirectory import sCribDirectory
from Dongle import Dongle

class DeviceJanitor(Thread):
    '''
    this class will periodically check devices and update their status and status of 
    clusters
    '''

    _janitorPeriod = 2 # in seconds
    _devices = None  #sCribDirectory
    

    def run(self):
        log_trace('I', '0039', "Janitor started", detail="n/a")
        dev_dictOld = {}
        dev_dictNew = {}
        while True:
            # we enumerate for new devices
            self._devices.purge()
            deviceList = None
            try:
                deviceList = self.getDeviceList()
            except:
                #ERR407
                log_trace('I', '0040', "Error during getDeviceList() - unplugging", detail="n/a")
                continue
           
            (devices, dev_dictNew) = deviceList
            for key in dev_dictOld:
                if not (key in dev_dictNew):
                    # we remove the device
                    self._devices.deleteByName(key)
                    pass
                    
            dev_dictOld = dev_dictNew
                
            if devices:
                for device in devices:
                    # this creates a class instance for a new dongle - if it's a new one
                    if not self._devices.exists(device[1]): # this and next line - not clean, eventually rewrite
                        newRecord = self.newDevice(device[1])
                        if newRecord:
                            if self._devices.add(newRecord, self._queues): # only continue if adding worked
                                # assign a queue to the device
                                newRecord.assignQueue(self._queues[newRecord.getCluster()], 
                                  self._devices.getCluster(newRecord.getCluster()) )
            
                                # and start the device
                                thread = Thread(target = newRecord.execute)
                                thread.start()
                            else:
                                log_trace('W', '0041', "Device unplugged while being added", device=device[1])
                        else:
                            log_trace('W', '0042', "Device unplugged while being initialised", device=device[1])
                            #ERR119
                    else:
                        #self._devices.reopen(device[1])
                        pass  
            else:
                pass # end of if devices:       
            # Sleep for a pre-defined time
            log_trace('D', '0043', "Janitor sleeping", process=self.getName(), interval=self._janitorPeriod)
            time.sleep(self._janitorPeriod)
            log_trace('D', '0044', "Janitor wakes", process=self.getName())

    def getDevices(self, cluster):
        log_trace('I', '0045', "getDevices() called", detail="n/a")
        return self._devices.getClusterDevices(cluster)

    def getDeviceList(self):
        """
        return a list of lines, each a colon-separated
        vendor:product:serial summary of detected devices
        """
        devices =  Dongle.listDevices()
        if devices is None:
            log_trace('I', '0046', "No devices connected", detail="n/a")
            return ([], [])
        else:
            return devices


    def newDevice(self,deviceName):
        
        # here is actual code we want!!!
        try:
            stick = Dongle(deviceName) #create the hardware
            if (stick):
                dongle = DeviceRecord(stick) # add hardware to DeviceRecord 
                log_trace('I', '0047', "New device added", name=deviceName)
                return dongle
            else:
                log_trace('I', '0048', "New device cannot be identified (ID, CLUSTER)", name=deviceName)
                # ERR_EXCEPTION ERR401
                return None
        except TypeError, e:
            # dongle not created
            log_trace('E', '0049', "Exception while adding device", name=deviceName, exception=e)
            # ERR_MALFUNCTION ERR402
            return None
        

    def __init__(self, queues):
        '''
        Constructor - the first device enumeration
        '''
        log_trace('D', '0050', "Janitor's constructor entered", detail="n/a")
        self._devices = sCribDirectory()
        self._queues = queues
            
        Thread.__init__(self)
        log_trace('I', '0051', "Janitor initialised", detail="n/a")
