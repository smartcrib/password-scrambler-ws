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
from pylibftdi import Device
#import sys


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
            pass #self.stick = Device(mode = "t")
        else:
            try:
                self._stick = Device(device_id=deviceId,mode = "t")
                self._stick.baudrate = 76800
                self._stick.open()
            except:
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
                self._stick.close()
                self._stick = None
                # ERR405
                return
                
            self._Cluster = self.GETCLUSTER()
            if self._Cluster:
                self._Cluster = self._Cluster.split()[0]
            else:
                self._stick.close()
                self._stick = None
                #ERR406
                return
            
            if (self._ID[:3]=="ERR") or (self._Cluster[:3]=="ERR"):
                self._stick.close()
                self._stick = None

    def exists(self):
        if self._stick:
            return True
        else:
            return False
    
    def _encrypt(self, message, passphrase):
        # passphrase MUST be 16, 24 or 32 bytes long, how can I do that ?
        IV =  "\x00" * self._BLOCK_SIZE
        while (len(passphrase)<32):
            passphrase = passphrase + "\x00"

        aes = AES.new(passphrase, AES.MODE_CBC, IV)
        return aes.encrypt(message)

    def _decrypt(self, encrypted, passphrase):
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
        try:
            self._stick.flush()
            #time.sleep(0.1)
            length = self._stick.write(cmd)
            #time.sleep(0.1)
            return length
        except:
            print("Device unplugged %s - write"% self.ID())
            #ERR410
            return None


    def _readData(self,replyLength):
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
                print("Timeout on reading - dongle %s (%f seconds)"%(self._HWID, delta))
                return None
            #if data[0:3] == "ERR":
            #    self.errorFlag = True
            #    self.errorMSg = data
            #    #self.stick.flush()
            #    #time.sleep(0.25)
            print("Data %s read in %f seconds"%(data.strip(), delta))
            return data
        except:
            print("No data to read from device %s"%self.ID())
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
        self._stick.close()
        self._stick.open()
#    Management Commands 

    def GETINITKEY(self):
        self.firstCmd = False
        (_,result) = (self._writeCmd((self.getInitKeyText)),self._readData(self.getInitKeyTextLen))
        if result:
            return result
        else:
            return None
        
    def GETPASSWD(self, index):
        
        try:
            passwordIndex = int(index,10)
        except:
            print("Password index must be an Integer")
            return "ERR104"

        if passwordIndex >= 2 and passwordIndex <= 4:
            self._stick.flush()
            (_,result) = (self._writeCmd((self.getPasswordText %passwordIndex)),self._readData(self.getPasswordTextLen))
            if result:
                return result
            else:
                return None
        else:
            print("Password index must be 2/3/4 not: %d" %passwordIndex)
            return "ERR103"

#    Status Commands
        

    def GETID(self):
        self.firstCmd = False
        (_, result) = (self._writeCmd(self.getIdText),self._readData(self.getIdTextLen))
        # add logging here
        if result:
            dongle = result
        else:
            dongle = None
        return dongle

        

    def GETCLUSTER(self):
        self.firstCmd = False
        (_, result) = (self._writeCmd(self.getClusterText),self._readData(self.getClusterTextLen))
        # add logging here
        if result:
            return result
        else:
            return None



    def GETLOCKED(self):
        self.firstCmd = False
        (_, result) = (self._writeCmd(self.getLockedText),self._readData(self.getLockedTextLen))
        # add logging here
        if result:
            return result
        else:
            return None

    def ENGETID(self, dongleID, data):
        self.firstCmd = False
        (_, result) = (self._writeCmd(self.enGetIdText%data),self._readData(self.enGetIdTextLen))
        # add logging here
        if result:
            enID = result
        else:
            enID = None
        return enID
        
    def GETCOUNTER(self):
        self.firstCmd = False
        (_, result) = (self._writeCmd(self.getCounterText),self._readData(self.getCounterTextLen))
        if result:
            result  = result
        else:
            result = None
        return result
        
    def GETDELAY(self):
        self.firstCmd = False
        (_, result) =  (self._writeCmd(self.getDelayText),self._readData(self.getDelayTextLen))
        if result:
            result  = result
        else: 
            result = None
        return result        
#    Execution Commands
    
    def SCRAMBLE(self, password, saltLength=0, salt=""):
        self.firstCmd = False
        if self._isASCII(password):
            if isinstance(saltLength,(int)):
                if saltLength >=0 and saltLength <=32:
                    if salt == "" or len(salt) == saltLength:
                        (_, result) =  (self._writeCmd(self.scrambleText %(password,saltLength,salt)),
                                self._readData(self.getDelayTextLen + saltLength + self.scrambleLength ))
                        if (result):
                            result  = result
                        else:
                            result = None
                        return result
                    
                    print(ValueError("Salt length : %d does not match the length of the salt supplied: %s" %(saltLength,len(salt))))
                    return "ERR105"
                else:
                    print("Salt length must be between 0 and 32 not: %d" %saltLength)
                    return "ERR106"
            else:
                print("Salt Length must be an Integer")
                return "ERR107"
        else:
            print("Password must be in ASCII")
            return "ERR108"
        
        
    def _ENSCRAMBLE(self, passphrase, serverCounter, password, saltLength=0, salt=""):
        # create the encrypted packet
        if len(serverCounter)>10:
            print("Server counter can be only 10 characters long - ENSCRAMBLE")
            return "ERR109"
            
        message = serverCounter.ljust(10) + " " + password.strip() + " "
        if not isinstance(saltLength, (int)):
            print("salt length must be an INT")
            return "ERR107"
        if saltLength<0 or saltLength > 16: 
            print("salt length must be between 0 and 16 not: %s" % saltLength)
            return "ERR106"
        if (saltLength != len(salt)) and (len(salt)>0):
            print("salt is not of expected length" % saltLength)
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
        result = result.encode("ascii","ignore")
        # the result must be terminated with '\n'
        data = binascii.unhexlify(result.strip())
        result = self._decrypt(data, passphrase)
        if (len(result)>0):
            if (serverCounter.ljust(11)!=result[:11]): #check the server challenge
                print("Server counter is incorrect IN: %s, OUT %s " % (serverCounter.ljust(10),result[:10]))
                return "ERR301"

            index = 11
            password = binascii.hexlify(result[index:(index+20)]).upper()
            index += 20
            salt = result[index:(index+saltLength)]
            index += saltLength
            counter = (((ord(result[index])*256+ord(result[index+1]))*256+ord(result[index+2]))*256+ord(result[index+3]))
            return (password, salt, counter)
        else:
            print("No data returned")
            return "ERR302"
        
                
    def ENSCRAMBLE(self,request):
        self.firstCmd = False
        if len(request)==128:
            (_, result) = (self._writeCmd((self.enScrambleText %request)),self._readData(self.enScrambleTextLen))
            result  = result
            return result
        else:
            print("Encrypted block must be 128 characters long")
            return "ERR130"
                
    def process(self, request):
        
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
                    data = "ERR111"
                else:
                    saltLength = int (request_bits[2])
                    if len(request_bits)==3:
                        data = self.SCRAMBLE(request_bits[1], saltLength)
                    elif len(request_bits)==4:
                        data = self.SCRAMBLE(request_bits[1], saltLength, request_bits[3])
                    else:
                        data = "ERR111"
            elif command == 11: #'ENSCRAMBLE':11,
                data = self.ENSCRAMBLE(request_bits[1])
            else:
                data = "ERR112"
        except:
            data = "ERR113"
            
        return data


        
