#!/usr/bin/python

"""scribManager.py: a class that opens a TCP server listening for requests from RESTfull top layer:
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
from shmLogging import log_trace, log_use
from QueueManager import QueueManager
from threading import BoundedSemaphore
from sCribClients import sCribClients
import SocketServer
import time
import re
import platform

_clients = None


'''
# This is the main class for the internal S-CRIB Manager
'''
class scribManager(SocketServer.BaseRequestHandler):

    def handle(self):
        self._verified = None
	self._apiExists = None
        self._success = False  # whether the processing has been completed or not
        self._request = ''
        self._response = ''
        self._apicommand = False
        self._semaphore = BoundedSemaphore(value=1)
        self.cur_thread = None
        
        data = ''
        try:
            while not (('\n' in data) or ('\r' in data)):
                data = data + self.request.recv(1024)
        except: #if there is an error while reading, just exit
            return
        
        data = data.replace("\b", "")
        log_trace('I', '0005', "Request received", detail=data)
        self._request = data.strip()+'\n'

        #server.queueManager      
        self.cur_thread = threading.current_thread()
        log_trace('D', '0006', "Request received", detail = self.cur_thread.name, data = self._request)
        
        if  self._verified is None:
            self.testRequest()
            
        if self._verified == False:
           if len(self._response) < 6:
               log_trace('D', '0007', "Incorrect internal verification response", detail = self.cur_thread.name, data = self._response)
               self._response = "ERR204"
           self.request.sendall(self._response) 
            
        self._semaphore.acquire()
        #insert itself to the Queue manager
        self.server.queueManager.newRequest(self._request, self.callback)
        
        #block till semaphore is open again
        self._semaphore.acquire()

        if self._success:
            log_trace('D', '0014', "Success - sendall() called", response=self._response)
            self.request.sendall(self._response)
        elif self._apicommand:
            #finally we can do API command processing here
            self._response = self.processAPICommand(self._response)
            self.request.sendall(self._response)
        else:
            if len(self._response) < 6:
                log_trace('C', '0013', "Incorrect result from request processing", detail=self._response, command=self._request)
                self._response = "ERR204"
            #TODO call a class constructor and block till its processing is completed
            self.request.sendall(self._response)
        self._semaphore.release()
       

     
    def callback(self, success, response):
        
        returned = response.split(' ',1)
        #ERR211 = API command -> no processing in secure HW
	if (len(returned)==2) and (returned[0]=="ERR211"):
            self._apicommand = True
            self._response = returned[1].strip()
            self._success = False
        else:
            self._response = response
            self._success = success

        log_trace('D', '0015', "Request processing successful - callback complete", detail="n/a")
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
            log_trace('C', '0008', "List of clients not initialised", detail = self.cur_thread.name)
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
                log_use('0004', "Unknown client", detail = self.cur_thread.name, client = requestItems[1])
                self._response = "ERR207" 
                return False

    def processAPICommand(self, command = None):
        if command is None:
            log_trace('C', '0009', "No command passed for processing", detail ="n/a")
            return "ERR208"
        splitcmd = command.split(' ')
	if len(splitcmd)<2:
            log_trace('C', '0010', "Incorrect command format passed for processing", detail=command)
            return "ERR204"

        api = splitcmd[1].strip()
        if int(splitcmd[0])==201:
            log_trace('D', '0011', "ADD API Command received", detail=command)
            #ADDAPICOMMAND
	    result = _clients.addClient(api)
        elif int(splitcmd[0])==202:
            log_trace('D', '0012', "CHECK API command received", detail=command)
            #CHECKAPICOMMAND
            result = _clients.checkClient(api)
        else:
            log_use('0005', "Unknown API command received", detail=command)
            result = "ERR211"

        return result
                
        
class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        log_trace('I', '0016', "ThreadedTCPServer - constructor", detail="n/a")
        self.queueManager = QueueManager()
        log_trace('I', '0034', "QueueManager created", detail="n/a")

        self.queueManager.processing()
        log_trace('I', '0035', "QueueManager started", detail="n/a")

if __name__ == '__main__':
    _backup = "api_clients.cfg"
  
    log_trace('I', '0001', "System configuration", uname = ', '.join(platform.uname()))
    log_trace('I', '0002', "Python version", python=platform.python_version())

    _clients = sCribClients(_backup)
    HOST, PORT = "localhost", 4241
    started = False
    while not started:
        try:
            server = ThreadedTCPServer((HOST, PORT), scribManager)
            started = True
        except:
            log_trace('C', '0003', "Cannot start server", detail="Possibly the port is already in use.")
            time.sleep(1)
            pass #try again after 1 second

    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    
    #server_thread.daemon = True
    server_thread.start()
    log_trace('I', '0004', "Server started", detail="Server's thread is"+server_thread.name)
    
    
    #server.shutdown()
    
