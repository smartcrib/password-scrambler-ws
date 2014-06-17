scribREST - outward looking RESTful service, opens internal TCP connection for 

scribManager - TCP incoming requests from top layer; accepts requests, create instances of Handler with callbacks
QueueManager - accepts requests and passes them on to appropriate queues of requests 
DeviceRecord - class for storing information about hardware device, it also runs a thread for each device, that checks the
       queue of requests and forwards requests to its device for processing

// independent thread looking after hardware
DeviceJanitor - periodically checks devices and updates status as necessary, creates DeviceRecords and assigns them to queues
       of requests
Dongle - actual interface to hardware devices, it is created as part of DeviceRecord instances

// data class
Errors - definition of errors
sCribClients - definition of clients allowed to use S-CRIB Manager
sCribDirectory - directory of all devices, and their clusters


START
1. scribManager is started and it spawns TCPServer and QueueManager
2. TCPServer gets ready for requests from rest (outbound facing restfull API)
3. QueueManager creates a storage class Queues() starts DeviceJanitor()
4. QueueManager is ready to accept data from TCPServer()
5. DeviceJanitor scans tokens and creates Queues for each "cluster" of dongles - data is fed into sCribDictionary
      - 2 structures: a) Clusters - dictionary of lists b) Devices
      - both structure contain pointers to class instances with open serial ports to dongles
6. With each new "cluster", a OneQueue() instance is created into the dictionary Queues()

INSTALL - LINUX

1. Create user scrib in its own group scrib.
2. Copy all files into the scrib user HOME folder - e.g., /home/scrib .
3. Find or create user that is used for web server - e.g. www-data, or www-scrib, if you create a new one.
4. Update DAEMONUSER in scribrestfull to the name from step 2.
5. copy files scribmanager and scribrestfull to folder /etc/init.d - you need root privileges
6. set access rights for files
     sudo chmod 755 /etc/init.d/scribmanager
     sudo chmod 755 /etc/init.d/scribrestfull
     sudo chmod 755 /home/scrib/scribManager.py
     sudo chmod 755 /home/scrib/scribREST.py

   and make sure all files in /home/scrib are owned by user scrib
     sudo chown scrib:scrib *
   except for the scribREST.py file ...
     sudo chown www-scrib:www-scrib *
7. You will need a few Python dependencies: pycrypto, pylibftdi, gevent, and greenlet - install then
8. Install monit, if you want to automatically restart the S-CRIB Manager after crash. 
   Copy the contents of monit* files into your monitrc file
