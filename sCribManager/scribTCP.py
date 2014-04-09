#!/usr/bin/python

"""scribTCP.py: a class that opens a TCP server listening for requests from RESTfull top layer:
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
import threading
import SocketServer
from QueueManager import QueueManager
from threading import BoundedSemaphore
from sCribClients import sCribClients
import re

_clients = None

class scribTCPServer(SocketServer.BaseRequestHandler):

    def handle(self):
        self._verified = None
	self._apiExists = None
        self._success = False  # whether the processing has been completed or not
        self._request = ''
        self._response = ''
        self._apicommand = False
        self._semaphore = BoundedSemaphore(value=1)
        
        
        data = ''
        try:
            while not (('\n' in data) or ('\r' in data)):
                data = data + self.request.recv(1024)
        except: #if there is an error while reading, just exit
            return
        
        data = data.replace("\b", "")
        print("InternalTCP - request received: %s"%data)
        self._request = data.strip()+'\n'

        #server.queueManager      
        cur_thread = threading.current_thread()
        print(cur_thread.name+" received "+self._request)
        
        if  self._verified is None:
            self.testRequest()
            
        if self._verified == False:
           if len(self._response) < 6:
               self._response = "ERR204"
           self.request.sendall(self._response) 
            
        self._semaphore.acquire()
        #insert itself to the Queue manager
        self.server.queueManager.newRequest(self._request, self.callback)
        
        #block till semaphore is open again
        self._semaphore.acquire()

        if self._success:
            self.request.sendall(self._response)
        elif self._apicommand:
            #finally we can do API command processing here
            self._response = self.processAPICommand(self._response)
            self.request.sendall(self._response)
        else:
            if len(self._response) < 6:
                self._response = "ERR204"
            #TODO call a class constructor and block till its processing is completed
            self.request.sendall(self._response)
        self._semaphore.release()
       

    def callback(self, success, response):
        
        returned = response.split(' ',1)
	if (len(returned)==2) and (returned[0]=="ERR211"):
            self._apicommand = True
            self._response = returned[1].strip()
            self._success = False
        else:
            self._response = response
            self._success = success

        #we have result, we can return it to the server
        self._semaphore.release()

    def testRequest(self):
        #test clusterID
        #test syntax
        request = re.sub( '\s+', ' ', self._request).strip()
        requestItems = request.split(" ")
        self._request = request
        if (not _clients):
            self._verified = False
            self._response = "ERR210"
            return False  #internal list of clients does not exist
            #raise ValueError("The API clients database has not been created yet - testRequest()")
        else :
            if (_clients.exists(requestItems[1])):
                requestItems[1] = _clients.getClusterID(requestItems[1])
                self._request = ' '.join(requestItems)
                self._verified = True
		self._apiExists = True
                return True
            else:
                self._verified = True 
                self._apiExists = False
                return False

    def processAPICommand(self, command = None):
        if command is None:
            return "ERR208"
        splitcmd = command.split(' ')
	if len(splitcmd)<2:
            return "ERR204"

        api = splitcmd[1].strip()
        if int(splitcmd[0])==201:
            #ADDAPICOMMAND
	    result = _clients.addClient(api)
        elif int(splitcmd[0])==202:
            #CHECKAPICOMMAND
            result = _clients.checkClient(api)
        else:
            result = "ERR211"

        return result
                
        
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    def __init__(self, server_address, RequestHandlerClass):
        self.queueManager = QueueManager()
        self.queueManager.processing()
        
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        

if __name__ == '__main__':
    _backup = "api_clients.cfg"
    
    _clients = sCribClients(_backup)
    HOST, PORT = "localhost", 4241
    server = ThreadedTCPServer((HOST, PORT), scribTCPServer)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    
    #server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread:", server_thread.name)
    
    
    #server.shutdown()
    
