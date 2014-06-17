#!/usr/bin/env python

"""sCribDirectory.py: a directory of hardware devices and their clusters:
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
from threading import Lock

class sCribDirectory(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self._DevicesHW = None
        self._Clusters = dict()
        self._Devices = dict()
   
    def __enter__(self):
        return self
            
    def reopen(self, device_id):
        if (self._DevicesHW.has_key(device_id)):
            self._Devices[self._DevicesHW[device_id]]['device'].reopen()
    
    def getCluster(self, clusterID):
        if clusterID in self._Clusters:
            return self._Clusters[clusterID]
        else:
            None  
           
    def getClusterDevices(self, clusterID):
        result = None
        if clusterID in self._Clusters:
            result = []
            for dev in self._Clusters[clusterID]:
                result.append(dev['id'])
        return result
            
    def exists(self, device_id):
        if self._DevicesHW is None:
            return False
        elif self._DevicesHW.has_key(device_id):
            return True
        else:
            return False
            
    def add(self, device, queues):
        
        if device == None:
            raise ValueError("No device specified")
        
        if device.getID() == None or device.getCluster() == None:
            print("Cluster (%s) and Token number (%s) must be specified" %(device.getID(), device.getCluster()))
            #ERR120
            return False

        if not self._DevicesHW is None:
            if self._DevicesHW.has_key(device.getHWID()):
                print("An entry already exists for token (%s / %s)!" %(device.getHWID(), device.getID()))
                #ERR121
                return False
        else: #create the dictionary if it doesn't exist 
            self._DevicesHW = dict()
            
        self._DevicesHW[device.getHWID()] = device.getID()
        self._Devices[device.getID()] = {'cluster':device.getCluster(), 'device':device, 'hwid': device.getHWID()}
        self.updated = True
        if not (device.getCluster() in self._Clusters.keys()):
            #we need to create a queue in the queues structure
            queues[device.getCluster()] = {'control': Lock(),'length': int, 'counter': int, 'requests':[]}
            queues[device.getCluster()]['length'] = 0
            queues[device.getCluster()]['counter'] = 0
            self._Clusters[device.getCluster()]=[]
                                
        self._Clusters[device.getCluster()].append({'id':device.getID(), 'device':device})
        queues[device.getCluster()]['counter'] += 2
        return True
    '''
    Remove devices that have been unplugged or are not available.
    We will purge such from all janitor data structures. 
    '''
    def purge(self):
        keys = self._Devices.keys()
        for key in keys:
            if key in self._Devices:
                # test if the device should be removed = it was unplugged
                if self._Devices[key]['device'].unplugged(): #its queue is Null 
                    #remove the device
                    cluster = self._Devices[key]['cluster']
                    hwid = self._Devices[key]['hwid']
                    del self._DevicesHW[hwid] #remove from list of HW ids
                    del self._Devices[key] # remove from list of IDs
                    #find the device in the cluster
                    found = False
                    for device in range(len(self._Clusters[cluster])):
                        if self._Clusters[cluster][device]['id']== key:
                            found = True
                            toDelete = device
                    if found:
                        del self._Clusters[cluster][toDelete]
                        
                    if len(self._Clusters[cluster])==0: # Shall we delete the cluster and all requests when no device is available?
                        pass #del self._Clusters[cluster]        
            
    def getToken(self,name):
        if self._Devices.has_key(name):
            return self._Devices[name]
        else:
            print("Name (%s) not found!" %name)
            #ERR122
            return None
        
    def getName(self,token):
        for name,tokenNumber in self._Devices.items():
            if token == tokenNumber:
                return name
        print("Token (%s) not found!" %token)
        #ERR123
        return None
    
    def deleteByName(self, hwname):
        
        if not self._DevicesHW:
            return
        
        if hwname in self._DevicesHW:
            name = self._DevicesHW[hwname]
            
            cluster = self._Devices[name]['cluster']
            del self._DevicesHW[hwname]
            del self._Devices[name]
            #find the device in the cluster
            found = False
            for device in range(len(self._Clusters[cluster])):
                if self._Clusters[cluster][device]['id']== name:
                    found = True
                    toDelete = device
            if found:
                del self._Clusters[cluster][toDelete]
            else:
                print("Integrity corruption - device not in cluster %s in %s"%(name, cluster))
                #ERR118 ERR_INTEGRITY
                        
            print("Device removed / unplugged %s from cluster %s"%(name, cluster))
            if len(self._Clusters[cluster])==0: # Shall we delete the cluster and all requests when no device is available?
                print("Cluster %s is empty"%cluster)
                pass #del self._Clusters[cluster]            
                
        
if __name__ == "__main__":
    
    with sCribDirectory() as sDict:
        sDict.add(cluster="george",tokenNumber="8mxaN*_d13")
        #print sDict.getToken("Dan")
    print sDict.getToken("george")
         
        
            
