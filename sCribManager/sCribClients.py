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

class sCribClients(object):
    '''
    classdocs
    '''
    
    def __init__(self, backup=None):
        '''
        Constructor
        '''
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
   
    def __enter__(self):
        return self

    
    def __exit__(self, *args, **kwargs):
        if self.updated:
            self.close() 

        
    def open(self):
        if self._backupFile is None:
            raise ValueError("No backup file defined for open()")
        elif self.directoryLoaded == True:
            raise ValueError("Directory of API clients already loaded.")
        else:
            #TODO add path check
            try:
                with open(self._backupFile, 'rb') as handle:
                    self._Directory = pickle.load(handle)
                    self.directoryLoaded = True
            except:
                print("File %s does not exist - open()"% self._backupFile) 
                self.directoryLoaded = True
                with open(self._backupFile, 'wb') as handle:
                    self.close()

    def persist(self):
        if self._backupFile is None:
            return
        elif not self.directoryLoaded:
            raise ValueError("Directory of API clients has not be loaded yet - persist()")
        else:
            with open(self._backupFile,'wb') as handle:
                pickle.dump(self._Directory, handle)
            
                
    def close(self):
        #TODO add Path check
        self.persist()
        

    def addClient(self, clusterID):
        print("Entered addClient()")
        if (clusterID is None):
            return "ERR209"
        elif len(clusterID)!=10:
            return "ERR209"
        else:
            found = False
            for key in self._Directory:
                if self._Directory[key]['cluster'] == clusterID:
                    found = True
            if found:
                return "ERR206" #API key exists
            else:
                random.seed() # seed with current time only
                apiKey = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(48))
                self.add(apiKey, clusterID)
                print("an API client created: "+apiKey)
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
         
        
            
