#!/usr/bin/env python
"""Dongle.py: a class interfacing a physical S-CRIB Scramble device accessible 
through pylibftdi library - project sCribManager - Python."""

'''
@author: Dan Cvrcek, George French
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''
from Crypto.Cipher import AES
import binascii
import time
from pylibftdi import Driver,Device
import sys
import traceback
from shmLogging import log_trace, log_use

class Dongle(object):
    '''
    
    For full description visit: http://docs.s-crib.com/doku.php/scramble_scrib_-_api_specification 
    
    Management commands
    GETINITKEY  host computer can request initialisation key, it will be typed after a button is pressed;
    GETPASSWD  requests one of the device's passwords.

    Status commands
    GETID  host computer requests the device's ID
    ENGETID  request the device's ID, the response is encrypted
    GETCOUNTER  returns the number of SCRAMBLE requests served

    Execution commands
    SCRAMBLE  protect a password;
    ENSCRAMBLE  protect a password that is sent encrypted

    General Rules and Security Policy
    1. Passwords contain characters in ASCII encoding.
    2. Management commands can only be executed before the first execution command is served.
    3. The maximum length of commands is 160 characters, including <new line>.
    4. All letters must be sent as capitals (with the exception of passwords), 
       the device replies with capital letters only as well.
    5. Commands must start immediately after newline, command and parameters must be separated 
       with exactly one space.
    6. The device does only necessary checks of commands and parameters to 
       protect itself against malformed commands.
    7. The device uses 3 passwords, each is 32 characters long:
        a, Password 2  for scrambling;
        b, Password 3  computes -time- to EXOR with salt before scrambling; and
        c, Password 4  encryption of parameters for commands with prefix EN.
    
    '''
    _BLOCK_SIZE = 16
    _READ_TIMEOUT = 2 # in seconds
    space = 1
    operationCounterLen = 8  + space # length of the postfix - appended to all non encrypted command responses
    scrambleLength = 64
        
    '''
    GETID command returns the device's ID. This is required to recover passwords
    from the initialisation key - online service is available here: https://my.s-crib.com/
    '''
    getIdText = "GETID\n"
    getIdTextLen  = 16 +operationCounterLen
        
    '''
    GETCLUSTER allows the host computer to request the device's cluster ID - identifies its set of passwords.
    '''
    getClusterText = "GETCLUSTER\n"
    getClusterTextLen = 10 +operationCounterLen
        
    '''
    GETLOCKED command returns whether the device is locked - protects keys/passwords. 
    '''
    getLockedText = "GETLOCKED\n"
    getLockedTextLen  = 1 +operationCounterLen
                
    '''
    GETINITKEY allows the host computer to request the device's initialisation key. 
    This can be printed out and used for pas < missing text on web site ;0)
    '''
    getInitKeyText = "GETINITKEY\n"
    getInitKeyTextLen = 48 +operationCounterLen
        
    '''
    GETPASSWD allows the host computer to request the device's passwords (2/3/4) for backup.
    '''
    getPasswordText = "GETPASSWD %d\n"
    getPasswordTextLen = 32 +operationCounterLen
        
    '''
    GETCOUNTER command returns the order number of the last command. 
    This counter is incremented with each command sent to the device. 
    It is kept in volatile memory and reset to nought each time the device loses power supply.
    '''
    getCounterText = "GETCOUNTER\n"
    getCounterTextLen = 16
        
    '''
    GETDELAY allows the host computer to set the current delay set on the device. 
    This delay may increase protection against brute-force attacks. 
    The delay is between 0 and 99. You need to experiment to get the delay length in milliseconds. 
    '''
    getDelayText = "GETDELAY\n"
    getDelayTextLen = 2 +operationCounterLen
        
    '''
    ENGETID is the encrypted variant of the GETID command. This can be used when the device is on another 
    physical server and some kind of encryption is required. 
    '''
    enGetIdText = "ENGETID %s\n"
    enGetIdTextLen = 64 +operationCounterLen
        
    '''
    ENSCRAMBLE is the encrypted variant of the SCRAMBLE command. 
    All parameters of SCRAMBLE are prefixed with a hexadecimal 
    counter of 16 digits and padded with spaces to create 96 characters' 
    string that is encrypted. Encryption used to protect parameters 
    is AES256-CBC and it uses Password 4
    '''
    enScrambleText = "ENSCRAMBLE %s\n"
    enScrambleTextLen = 128 +operationCounterLen
        
    '''
    This is the actual operation command. Password must not contain space or new line. 
    The salt_length is between 0 and 32 and denotes the length of the returned string. 
    The string is of hexadecimal digits and each digit gives 4 bits of entropy.
    The salt is an optional parameter with the minimum length of <salt_length>. 
    If the <salt> is missing and <salt_length> is non-zero, the device will generate 
    a new random <salt>. 
    '''
    scrambleText = "SCRAMBLE %s %02d %s\n"
    scrambleTextLen =operationCounterLen  # Length will need to adjusted at time of call
  
    def __init__(self,deviceId=""):
        '''
        Constructor
        '''
        self._ID = None
        self._HWID = None
        self._Cluster = None
        
        self._firstCmd = True
        self._errorFlag = False
        self._errorMSg = ""
        self._stick = None
        if deviceId == "":
            log_trace('C', '0067', "No deviceID provided", traceback=traceback.print_stack())
            pass #self.stick = Device(mode = "t")
        else:
            try:
                self._stick = Device(device_id=deviceId,mode = "t")
                self._stick.open()
                #one call of the baudrate setter does not always work 
                self._stick.baudrate = 3000000
            except:
                log_trace('E', '0068', "Error when opening new device", ID=deviceId, exception=', '.join(sys.exc_info()[0]))
                if self._stick:
                    self._stick.close()
                self._stick = None
                #ERR408
                return
            self._HWID = deviceId
            self._ID = self.GETID()
            if self._ID:
                self._ID = self._ID.split()[0]
            else:
                log_trace('E', '0069', "GETID() returned no data", HWID=deviceId)
                self._stick.close()
                self._stick = None
                # ERR405
                return
                
            self._Cluster = self.GETCLUSTER()
            if self._Cluster:
                self._Cluster = self._Cluster.split()[0]
            else:
                log_trace('E', '0070', "GETCLUSTER() returned no data", HWID=deviceId)
                self._stick.close()
                self._stick = None
                #ERR406
                return
            
            if (self._ID[:3]=="ERR") or (self._Cluster[:3]=="ERR"):
                log_trace('E', '0071', "Device initialisation returned an error (GETID or GETCLUSTER)", HWID=deviceId, ID=self._ID, cluster=self._Cluster)
                self._stick.close()
                self._stick = None

    def exists(self):
        log_trace('D', '0072', "exists() called", ID=self._ID)
        if self._stick:
            return True
        else:
            return False

    ''' 
       Returns a list of tuples:
        - first item: a colon-separated vendor:product:serial summary of detected devices
        - second item: serial number - HWID
    '''
    @staticmethod  
    def listDevices():
        log_trace('D', '0073', "listDevices() called", detail="n/a")
        dev_list = []
        dev_dict = {}
        devices = None
        try:
            #FTDI returns a list of triplets - (vendor, name, HWID)
            devices =  Driver().list_devices()
        except AttributeError, e:
            # ERR_ENUMERATE ERR403
            log_trace('E', '0074', "Error when enumerating devices - Attribute Error", exception=e)
            if  not devices:
                return None
        except :
            # ERR_DRIVER ERR404
            log_trace('E', '0075', "Error when enumerating devices", exception=', '.join(sys.exc_info()[0]))
            if not devices:
                return None

        # expected response is an empty list - None may mean an error
        if not devices:
            log_trace('E', '0076', "list_devices() returned 'None'", detail="n/a")
            return None

        for device in devices:
            device = map(lambda x: x.decode('latin1'), device)
            vendor, product, serial = device
            dev_list.append(("%s:%s:%s" % (vendor, product, serial),serial))
            log_trace('D', '0077', "Device found", vendor=vendor, product=product, serial=serial)
            dev_dict[serial] = 1
        return (dev_list, dev_dict)


    def _encrypt(self, message, passphrase):
        log_trace('D', '0078', "_encrypt() called", detail="n/a")
        # passphrase MUST be 16, 24 or 32 bytes long, how can I do that ?
        IV =  "\x00" * self._BLOCK_SIZE
        while (len(passphrase)<32):
            passphrase = passphrase + "\x00"

        aes = AES.new(passphrase, AES.MODE_CBC, IV)
        return aes.encrypt(message)

    def _decrypt(self, encrypted, passphrase):
        log_trace('D', '0079', "_decrypt() called", detail="n/a")
        IV = "\x00" * self._BLOCK_SIZE
        while (len(passphrase)<32):
            passphrase = passphrase + "\x00"
            
        aes = AES.new(passphrase, AES.MODE_CBC, IV)
        result = aes.decrypt(encrypted)
        padding = ord(result[len(result)-1])
        length = len(result)
        for index in range(length-padding,length):
            if (ord(result[index]) != padding):
                return ""
        padding = length - padding # get data bytes instead of padding length
        result = result[:padding]
        return result
        

    def _writeCmd(self, cmd):
        log_trace('D', '0080', "_writeCmd() called", detail="n/a") 
        try:
            self._stick.flush()
            #time.sleep(0.1)
            length = self._stick.write(cmd)
            #time.sleep(0.1)
            return length
        except:
            log_trace('E', '0081', "Device unplugged when writing", ID=self._ID())
            #ERR410
            return None


    def _readData(self,replyLength):
        log_trace('D', '0082', "_readData() called", detail="n/a")
        try:
            data = ""
            started = time.time()
            delta = 0
            while (data.find('\x0a')<0):
                data = data+self._stick.read(160)  # maximum length that can be returned
                #sys.stdout.write(str(len(data))+'.')
                delta = time.time() - started
                if delta>self._READ_TIMEOUT:
                    self.errorFlag = True
                    break
                if data:
                    self.errorFlag = False
                    break
            if delta > self._READ_TIMEOUT:
                #ERR411
                log_trace('E','0083', "Timeout on reading", HWID=self._HWID, timeout=delta)
                return None
            #if data[0:3] == "ERR":
            #    self.errorFlag = True
            #    self.errorMSg = data
            #    #self.stick.flush()
            #    #time.sleep(0.25)
            log_trace('D', '0084', "Data read from device", data=data.strip(), latency=delta)
            return data
        except:
            log_trace('E', '0085', "Error when reading from device", ID=self._ID,exception=', '.join(sys.exc_info()[0]))
            #ERR409
            return None
        
    def _isASCII(self,data):
        try: 
            data.decode('ascii')
        except UnicodeDecodeError:
            return False
        except AttributeError:
            return False
        else:
            return True


    def ID(self):
        return self._ID
    
    def HWID(self):
        return self._HWID
    
    def CLUSTER(self):
        return self._Cluster
  
    def close(self):
        self._stick.close()
    
    def reopen(self):
        log_trace('D', '0086', "reopen() called", HWID=self._HWID)
        self._stick.close()
        self._stick.open()
#    Management Commands 

    def GETINITKEY(self):
        log_trace('D', '0087', "GETINITKEY() called", ID=self._ID)
        start=time.time()
        self.firstCmd = False
        (_,result) = (self._writeCmd((self.getInitKeyText)),self._readData(self.getInitKeyTextLen))
        latency=time.time()-start
        log_use('0009', "GETINITKEY", self._ID, "n/a", latency=latency)
        if result:
            return result
        else:
            return None
        
    def GETPASSWD(self, index):
        log_trace('D', '0088', "GETPASSWD() called", ID=self._ID, index=index)
        start = time.time()
        try:
            passwordIndex = int(index,10)
        except:
            log_trace('D', '0089', "GETPASSWD - wrong parameter", ID=self._ID, index=index)
            return "ERR104"

        if passwordIndex >= 2 and passwordIndex <= 4:
            self._stick.flush()
            (_,result) = (self._writeCmd((self.getPasswordText %passwordIndex)),self._readData(self.getPasswordTextLen))
            latency = time.time() - start
            log_use('0010', "GETPASSWD", self._ID, "n/a", latency=latency)
            if result:
                return result
            else:
                return None
        else:
            log_trace('D', '0090', "GETPASSWD - wrong parameter", ID=self._ID, index=index)
            return "ERR103"

#    Status Commands
        

    def GETID(self):
        log_trace('D', '0091', "GETID() called", ID=self._ID)
        start = time.time()

        self.firstCmd = False
        (_, result) = (self._writeCmd(self.getIdText),self._readData(self.getIdTextLen))
        latency = time.time() - start
        log_use('0011', "GETID", self._ID, "n/a", latency=latency)
        # add logging here
        if result:
            dongle = result
        else:
            dongle = None
        return dongle

        

    def GETCLUSTER(self):
        log_trace('D', '0092', "GETCLUSTER() called", ID=self._ID)
        start = time.time()
        self.firstCmd = False
        (_, result) = (self._writeCmd(self.getClusterText),self._readData(self.getClusterTextLen))
        latency = time.time() - start
        log_use('0012', "GETCLUSTER",  self._ID, "n/a",  latency=latency)
        # add logging here
        if result:
            return result
        else:
            return None



    def GETLOCKED(self):
        log_trace('D', '0093', "GETLOCKED() called", ID=self._ID)
        start = time.time()
        self.firstCmd = False
        (_, result) = (self._writeCmd(self.getLockedText),self._readData(self.getLockedTextLen))
        # add logging here
        latency = time.time() - start
        log_use('0013', "GETLOCKED",  self._ID, "n/a", latency=latency)
        if result:
            return result
        else:
            return None

    def ENGETID(self, dongleID, data):
        log_trace('D', '0094', "ENGETID() called", ID=self._ID, dongle = dongleID, data=data)
        start = time.time()
        (_, result) = (self._writeCmd(self.enGetIdText%data),self._readData(self.enGetIdTextLen))
        # add logging here
        latency = time.time() - start
        log_use('0014', "ENGETID",  self._ID, "n/a",  dongle=dongleID, data=data, latency=latency)
        if result:
            enID = result
        else:
            enID = None
        return enID
        
    def GETCOUNTER(self):
        log_trace('D', '0095', "GETCOUNTER() called", ID=self._ID)
        start = time.time()
        (_, result) = (self._writeCmd(self.getCounterText),self._readData(self.getCounterTextLen))
        latency = time.time() - start
        log_use('0015', "GETCOUNTER",  self._ID, "n/a",  latency=latency)
        if result:
            result  = result
        else:
            result = None
        return result
        
    def GETDELAY(self):
        log_trace('D', '0096', "GETDELAY() called", ID=self._ID)
        start = time.time()
        (_, result) =  (self._writeCmd(self.getDelayText),self._readData(self.getDelayTextLen))
        latency = time.time() - start
        log_use('0016', "GETDELAY",  self._ID, "n/a", latency=latency)
        if result:
            result  = result
        else: 
            result = None
        return result        
#    Execution Commands
    
    def SCRAMBLE(self, password, saltLength=0, salt=""):
        log_trace('D', '0097', "SCRAMBLE() called", ID=self._ID)
        start = time.time()
        if self._isASCII(password):
            if isinstance(saltLength,(int)):
                if saltLength >=0 and saltLength <=32:
                    if salt == "" or len(salt) == saltLength:
                        (_, result) =  (self._writeCmd(self.scrambleText %(password,saltLength,salt)),
                                self._readData(self.getDelayTextLen + saltLength + self.scrambleLength ))
                        latency = time.time() - start
                        log_use('0017', "SCRAMBLE",  self._ID, "n/a", latency=latency)
                        if (result):
                            result  = result
                        else:
                            result = None
                        return result
                    log_trace('D', '0098', "Salt length does not match the length of the salt supplied.", saltLength=saltLength, salt=salt) 
                    return "ERR105"
                else:
                    log_trace('D', '0099', "Salt length must be between 0 and 32", ID=self._ID, saltLength=saltLength)
                    return "ERR106"
            else:
                log_trace('D', '0100', "Salt length must be integer", ID=self._ID, saltLength=saltLength)
                return "ERR107"
        else:
            log_trace('D', '0101', "Password must be in ASCII encoding", ID=self._ID)
            return "ERR108"
        
        
    def _ENSCRAMBLE(self, passphrase, serverCounter, password, saltLength=0, salt=""):
        # create the encrypted packet
        log_trace('D', '0102', "Test _ENSCRAMBLE() called", ID=self._ID)
        start = time.time()
        if len(serverCounter)>10:
            log_trace('D', '0103', "Server counter can be only 10 characters long - ENSCRAMBLE", ID=self._ID, counter=serverCounter)
            return "ERR109"
            
        message = serverCounter.ljust(10) + " " + password.strip() + " "
        if not isinstance(saltLength, (int)):
            log_trace('D', '0104', "Salt length must be integer", ID=self._ID, saltLength=saltLength)
            return "ERR107"
        if saltLength<0 or saltLength > 16: 
            log_trace('D', '0105', "Salt length must be between 0 and 16", ID=self._ID, saltLength=saltLength)
            return "ERR106"
        if (saltLength != len(salt)) and (len(salt)>0):
            log_trace('D', '0106', "Salt length does not match the length of the salt supplied", ID=self._ID, saltLength=saltLength, salt=salt)
            return "ERR105"

        message = message + "%02d"%saltLength
        if len(salt)>0:
            message = message +" "+salt
            
        padding = 64 - len(message)
        data = list(message+ "\x00"*padding)
        for i in range(64-padding, 64):
            data[i] = chr(padding)
    
        data = "".join(data)
        result = self._encrypt(data, passphrase)
        dataToSend = binascii.hexlify(result).upper()

        # call the dongle
        (_, result) = (self._writeCmd(self.enScrambleText % dataToSend), self._readData(self.enScrambleTextLen ))
        latency = time.time() - start
        log_use('0018', "Test _ENSCRAMBLE",  self._ID, "n/a", latency=latency)
        result = result.encode("ascii","ignore")
        # the result must be terminated with '\n'
        data = binascii.unhexlify(result.strip())
        result = self._decrypt(data, passphrase)
        if (len(result)>0):
            if (serverCounter.ljust(11)!=result[:11]): #check the server challenge
                log_trace('D', '0107', "Server counter is incorrect", ID=self._ID, counterIn=serverCounter.ljust(10), counterOut=result[:10])
                return "ERR301"

            index = 11
            password = binascii.hexlify(result[index:(index+20)]).upper()
            index += 20
            salt = result[index:(index+saltLength)]
            index += saltLength
            counter = (((ord(result[index])*256+ord(result[index+1]))*256+ord(result[index+2]))*256+ord(result[index+3]))
            return (password, salt, counter)
        else:
            log_trace('D', '0108', "No data returned", ID=self._ID, counter=serverCounter, saltLength=saltLength, salt=salt, password=password, pwd4=passphrase)
            return "ERR302"
        
                
    def ENSCRAMBLE(self,request):
        log_trace('D', '0109', "ENSCRAMBLE() called", ID=self._ID)
        start = time.time()
        self.firstCmd = False
        if len(request)==128:
            (_, result) = (self._writeCmd((self.enScrambleText %request)),self._readData(self.enScrambleTextLen))
            latency = time.time() - start
            log_use('0019', "ENSCRAMBLE",  self._ID, "n/a", latency=latency)
            return result
        else:
            log_trace('D', '0110', "Request data must be 128 bytes long", ID=self._ID, request=request)
            return "ERR130"
                
    def process(self, request):
        log_trace('D', '0111', "process() called", ID=self._ID, request=request) 
        request_bits = request.split()
        command = int(request_bits[0])
        try:
            if command == 2: #'GETINITKEY':2,
                data = self.GETINITKEY(request_bits[1])
            elif command == 3: #'GETPASSWD':3,
                data = self.GETPASSWD(request_bits[1])
            elif command == 4: #'GETID':4,
                data = self.GETID()
            elif command == 5: #'ENGETID':5,
                if len(request_bits) < 3:
                    data = "ERR125"
                else:
                    data = self.ENGETID(request_bits[1], request_bits[2])
            elif command == 6: #'GETCOUNTER':6,
                data = self.GETCOUNTER()
            elif command == 7: #'GETDELAY':7,
                data = self.GETDELAY()
            elif command == 8: #GETCLUSTER':8,
                data = self.GETCLUSTER()
            elif command == 9: #'GETLOCKED':9,
                data = self.GETLOCKED()
            elif command == 10: #'SCRAMBLE':10,
                if len(request)<3:
                    log_trace('D', '0112', "SCRAMBLE - incorrect number of params", params=len(request))
                    data = "ERR111"
                else:
                    saltLength = int (request_bits[2])
                    if len(request_bits)==3:
                        data = self.SCRAMBLE(request_bits[1], saltLength)
                    elif len(request_bits)==4:
                        data = self.SCRAMBLE(request_bits[1], saltLength, request_bits[3])
                    else:
                        log_trace('D', '0113', "SCRAMBLE - incorrect number of params", params=len(request))
                        data = "ERR111"
            elif command == 11: #'ENSCRAMBLE':11,
                data = self.ENSCRAMBLE(request_bits[1])
            else:
                log_trace('D', '0114', "Unknown command", command=command)
                data = "ERR112"
        except:
            log_trace('E', '0115', "Exception in process()", exception=', '.join(sys.exc_info()[0]), request=request)
            data = "ERR113"
            
        return data
        
