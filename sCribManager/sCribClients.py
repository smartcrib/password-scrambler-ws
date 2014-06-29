#!/usr/bin/env python

"""sCribClients.py: a directory of API keys and clusters of hardware devices:
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

import pickle
import random
import string
from shmLogging import log_trace, log_use

class sCribClients(object):
    '''
    classdocs
    '''
    
    def __init__(self, backup=None):
        '''
        Constructor
        '''
        log_trace('I', '0116', "sCribClients - constructor", detail="n/a")
        self._backupFile = None
        self._Directory = dict()

        
        self.directoryLoaded = False
        self.updated = False  #when True, the copy in memory is newer than the disk copy
        if backup == None:
            self._Directory = dict()
            self.directoryLoaded = True
        else:
            self._backupFile = backup
            self._Directory = dict()
            self.open()
            self.directoryLoaded = True
        log_trace('I', '0117', "sCribClients - constructor completed", detail="n/a")
   
    def __enter__(self):
        return self

    
    def __exit__(self, *args, **kwargs):
        log_trace('I', '0118', "sCribClients - destructor", detail="n/a")
        if self.updated:
            self.close() 

        
    def open(self):
        if self._backupFile is None:
            log_trace('C', '0119', "No backup file defined for open() - sCribClients", detail="n/a")
            raise ValueError("No backup file defined for open()")
        elif self.directoryLoaded == True:
            log_trace('E', '0120', "Directory of API clients already loaded", detail="n/a")
            raise ValueError("Directory of API clients already loaded.")
        else:
            #TODO add path check
            try:
                with open(self._backupFile, 'rb') as handle:
                    self._Directory = pickle.load(handle)
                    self.directoryLoaded = True
            except:
                log_trace('I', '0121', "File does not exist - open() - we create it", filename=self._backupFile)
                self.directoryLoaded = True
                with open(self._backupFile, 'wb') as handle:
                    self.close()
        

    def persist(self):
        if self._backupFile is None:
            return
        elif not self.directoryLoaded:
            log_trace('C', '0124',"Directory of API clients has not be loaded yet - persist()", filename=self._backupFile) 
            raise ValueError("Directory of API clients has not be loaded yet - persist()")
        else:
            with open(self._backupFile,'wb') as handle:
                pickle.dump(self._Directory, handle)
        log_trace('D', '0123', "Clients saved to disk file", filename=self._backupFile)    
                
    def close(self):
        #TODO add Path check
        self.persist()
        

    def addClient(self, clusterID):
        start = time.time()
        log_trace('D', '0125', "Entered AddClient()", detail="n/a")
        if (clusterID is None):
            log_trace('I', '0126', "No clusterID provided", cluster=clusterID)
            return "ERR209"
        elif len(clusterID)!=10:
            log_trace('I', '0127', "Incorrect clusterID length", cluster=clusterID)
            return "ERR209"
        else:
            found = False
            for key in self._Directory:
                if self._Directory[key]['cluster'] == clusterID:
                    found = True
            if found:
                log_trace('I', '0128', "Cluster already registered", cluster=clusterID)
                return "ERR206" #API key exists
            else:
                random.seed() # seed with current time only
                apiKey = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(48))
                self.add(apiKey, clusterID)
                latency = time.time() - start
                log_use('0020', "ADDCLIENT", clusterID, "n/a", latency=latency, apikey=apiKey)
                return apiKey+" "+clusterID 

    def checkClient(self, clusterID):
        if (clusterID is None):
            return "ERR209"
        elif len(clusterID)!=10:
            return "ERR209"
        else:
            found = None
            for key in self._Directory:
                if self._Directory[key]['cluster'] == clusterID:
                    found = key
            if found is None:
                return "ERR207" 
            else:
                return found  
 
    def add(self, apikey, clusterID, info=None):
        
        if (apikey == None) or (clusterID == None):
            raise ValueError("Required API information is not provided - add()")
        
        if self._Directory.has_key(apikey):
            print("An entry already exists for API client (%s)!" % apikey)
            #ERR206
            return 

        self._Directory[apikey] = {'cluster':clusterID, 'info':info}
        self.updated = True

        try:
            self.persist()
            self.updated = False
        except:
            pass
        
    def exists(self, apikey):
        if (self._Directory):
            if (apikey in self._Directory):
                return True
            else:
                return False
        else:
            raise ValueError("The database of API clients not initialised")
 
    def getClusterID(self, apikey):
        if (self._Directory):
            if apikey in self._Directory:
                return self._Directory[apikey]['cluster']
            else:
                return None
        else:
            raise ValueError("The database of API clients not initialised")
        
        
    def getAPIDetails(self, apikey):
        if self._Directory.has_key(apikey):
            return self._Directory[apikey]['info']
        else:
            return None
    
    def deleteByName(self, apikey):
        try:
            if self._Directory.has_key(apikey):
                self._Directory.pop(apikey)
                self.updated = True
                self.persist()
                self.updated = False
        except:
            print("API key does not exist - deleteByName()")
            #ERR207
        
        
if __name__ == "__main__":
    
    with sCribClients("api_clients.cfg") as sDict:
        # d = sDict()
        sDict.add(apikey="george",clusterID="hpIO%39-_l", info={'version':1, 'host':'localhost'})
        #print sDict.getToken("Dan")
    print sDict.getClusterID("george")
         
        
            
