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
        self._success = False  # whether the processing has been completed or not
        self._request = ''
        self._response = ''
        self._semaphore = BoundedSemaphore(value=1)
        
        
        data = ''
        try:
            while not (('\n' in data) or ('\r' in data)):
                data = data + self.request.recv(1024)
        except: #if there is an error while reading, just exit
            return
        
        data = data.replace("\b", "")
        print ("InternalTCP - request received: %s"%data)
        self._request = data.strip()+'\n'

        #server.queueManager      
        cur_thread = threading.current_thread()
        print cur_thread.name+" received "+self._request
        
        if  self._verified is None:
            self.testRequest()
            
        if self._verified == False:
            return False
            
        self._semaphore.acquire()
        #insert itself to the Queue manager
        self.server.queueManager.newRequest(self._request, self.callback)
        
        #block till semaphore is open again
        self._semaphore.acquire()

        if self._success:
            self.request.sendall(self._response)
        else:
            self.response = "ERRxxx"
            #TODO call a class constructor and block till its processing is completed
            self.request.sendall(self._response)
        
    def callback(self, success, response):
        
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
            raise ValueError("The API clients database has not been created yet - testRequest()")
        else :
            if (_clients.exists(requestItems[1])):
                requestItems[1] = _clients.getClusterID(requestItems[1])
                self._request = ' '.join(requestItems)
                self._verified = True
                return True
            else:
                self._verified = False
                return False
                
        
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
    print "Server loop running in thread:", server_thread.name
    
    
    #server.shutdown()
    
