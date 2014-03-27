#!/usr/bin/python
"""sc_driver.py: a class interfacing a physical S-CRIB Scramble device for command line 
utilities through pylibftdi library - project sCribManager - Python."""

'''
@author: George French
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''

from pylibftdi import Device, Driver
import time
import binascii
import sys

class sc_driver(object):
    '''
   
    This class supports only local commands - not encrypted versions and it talks to particular 
    S-CRIB Scramblers.
 
    For full description visit: http://docs.s-crib.com/doku.php/scramble_scrib_-_api_specification 
    
    Management commands
    SETINITKEY  host computer will send an initialisation key that will reinitialise the device, this must be done immediately after the device has been reset, i.e., 
                before any of the execution commands;command must be confirmed with a button press
    GETINITKEY  host computer can request initialisation key, it will be typed after a button is pressed;
    GETPASSWD  requests one of the device's passwords.

    Status commands
    GETID  host computer requests the device's ID
    GETCLUSTER  returns a 10 character cluster ID
    GETCOUNTER  returns the number of SCRAMBLE requests served
    GETDELAY  returns the current delay.
    GETLOCKED returns 1 if the initialisation phase has been closed

    Execution commands
    SETDELAY  set delay between SCRAMBLE requests; command must be confirmed with a button press.
    SCRAMBLE password scrambling command

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
    
    def __init__(self,deviceId=""):
        '''
        Constructor
        '''
        self.space = 1
        operationCounterLen = 8  + self.space 

        '''
        SETINITKEY Initialisation key is a string of 48 hexadecimal characters, 
        the exception are the first 8 characters that come from the set of 1-4.
        '''
        self.setInitKeyText = "SETINITKEY %s\n"
        self.setInitKeyTextLen = 8 + operationCounterLen
        
        '''
        GETINITKEY allows the host computer to request the device's initialisation key. 
        This can be printed out and used for pas < missing text on web site ;0)
        '''
        self.getInitKeyText = "GETINITKEY\n"
        self.getInitKeyTextLen = 48 + operationCounterLen
        
        '''
        GETID command returns the device's ID. This is required to recover passwords
        from the initialisation key - online service is available here: https://my.s-crib.com/
        '''
        self.getIdText = "GETID\n"
        self.getIdTextLen  = 16 + operationCounterLen
        
        '''
        GETLOCKED command returns whether the device is locked - protects keys/passwords. 
        '''
        self.getLockedText = "GETLOCKED\n"
        self.getLockedTextLen  = 1 + operationCounterLen
        
        '''
        GETCLUSTER allows the host computer to request the device's cluster ID - identifies its set of passwords.
        '''
        self.getClusterText = "GETCLUSTER\n"
        self.getClusterTextLen = 10 + operationCounterLen
        
        '''
        GETPASSWD allows the host computer to request the device's passwords (2/3/4) for backup.
        '''
        self.getPasswordText = "GETPASSWD %d\n"
        self.getPasswordTextLen = 32 + operationCounterLen
        
        '''
        GETCOUNTER command returns the order number of the last command. 
        This counter is incremented with each command sent to the device. 
        It is kept in volatile memory and reset to nought each time the device loses power supply.
        '''
        self.getCounterText = "GETCOUNTER\n"
        self.getCounterTextLen = 16 
        
        '''
        GETDELAY allows the host computer to set the current delay set on the device. 
        This delay may increase protection against brute-force attacks. 
        The delay is between 0 and 99. You need to experiment to get the delay length in milliseconds. 
        '''
        self.getDelayText = "GETDELAY\n"
        self.getDelayTextLen = 2 + operationCounterLen
        
        '''
        This is the actual operation command. Password must not contain space or new line. 
        The salt_length is between 0 and 32 and denotes the length of the returned string. 
        The string is of hexadecimal digits and each digit gives 4 bits of entropy.
        The salt is an optional parameter with the minimum length of <salt_length>. 
        If the <salt> is missing and <salt_length> is non-zero, the device will generate 
        a new random <salt>. 
        '''
        self.scrambleText = "SCRAMBLE %s %02d %s\n"
        self.scrambleTextLen = operationCounterLen  # Length will need to adjusted at time of call
  
        
        '''
        SETDELAY allows the Host computer to set additional delay between commands to protect against brute-force attacks. 
        The delay is between 0 and 99. You need to experiment to get the delay length in 
        milliseconds but it will be at least 10*<delay value> milliseconds. 
        '''
        self.setDelayText = "SETDELAY %s\n"
        self.setDelayTextLen = 2 + operationCounterLen
        
        
        self.firstCmd = True
        self.errorFlag = False
        self.errorMSg = ""
        if deviceId == "":
            #pass 
            self.stick = Device(mode = "t")

        else:
            self.stick = Device(device_id=deviceId,mode = "t")
            self.stick.baudrate = 76800
            self.stick.open()
        
    
    
    def getDeviceList(self):
        ''' 
        return a list of lines, each a colon-separated
        vendor:product:serial summary of detected devices
        '''
        dev_list = []
        devices = Driver().list_devices()
        for device in devices:
            device = map(lambda x: x.decode('latin1'), device)
            vendor, product, serial = device
            dev_list.append(("%s:%s:%s" % (vendor, product, serial),serial))
        return dev_list
  
    def close(self):
        self.stick.close()
    
#    Management Commands 
        
    def SETINITKEY(self,key):
        if self.firstCmd == True:
            #TODO set format check for first 8 being {1-4} and length 48
            if len(key) == 48:
                return (self.__writeCmd(self.setInitKeyText %key),self.__readData(self.setInitKeyTextLen))
                self.firstCmd = False
            else:
                raise ValueError("Must be 48 Hex characters in length not: %s" %len(key))
        else:
            raise ValueError("Must be first Command issued")
         
    def GETINITKEY(self):
        self.firstCmd = False
        len = self.stick.write("GETINITKEY\n")
        data = self.stick.read(48+8)
        return (len,data)
        
    def GETPASSWD(self, passwordIndex):
        
        if isinstance(passwordIndex,(int)):
            if passwordIndex >= 2 and passwordIndex <=4:
                self.stick.flush()
                return (self.__writeCmd((self.getPasswordText %passwordIndex)),self.__readData(self.getPasswordTextLen))
            else:
                raise ValueError("Password index must be 2/3/4 not: %d" %passwordIndex)
        else:
            raise TypeError("Password index must be an Integer")
#    Status Commands
        

    def GETCLUSTER(self):
        self.firstCmd = False
        return (self.__writeCmd(self.getClusterText),self.__readData(self.getClusterTextLen))


    def GETID(self):
        self.firstCmd = False
        return (self.__writeCmd(self.getIdText),self.__readData(self.getIdTextLen))

    def GETLOCKED(self):
        self.firstCmd = False
        return (self.__writeCmd(self.getLockedText),self.__readData(self.getLockedTextLen))


    def __writeCmd(self, cmd):
        self.stick.flush()
        len = self.stick.write(cmd)
        return len


    def __readData(self,replyLength):
        data=""
        data += self.stick.read(160)  # maximum length that can be returned
        while (data.find('\x0a')<0):
            data = self.stick.read(160)  # maximum length that can be returned
        if data[0:3] == "ERR":
            self.errorFlag = True
            self.errorMSg = data
        return data
        
    def __isASCII(self,data):
        try: 
            data.decode('ascii')
        except UnicodeDecodeError:
            return False
        except AttributeError:
            return False
        else:
            return True

    def GETCOUNTER(self):
        self.firstCmd = False
        return (self.__writeCmd(self.getCounterText),self.__readData(self.getCounterTextLen))
        
    def GETDELAY(self):
        self.firstCmd = False
        return (self.__writeCmd(self.getDelayText),self.__readData(self.getDelayTextLen))
        
#    Execution Commands
    
    def SCRAMBLE(self, password, saltLength=0, salt=""):
        self.firstCmd = False
        if self.__isASCII(password):
            if isinstance(saltLength,(int)):
                if saltLength >=0 and saltLength <=32:
                    if salt == "" or len(salt) == saltLength:
                        return (self.__writeCmd(self.scrambleText %(password,saltLength,salt)),
                                self.__readData(self.getDelayTextLen + saltLength + self.scrambleLength ))
                    raise ValueError("Salt length : %d does not match the length of the salt supplied: %s" %(saltLength,len(salt)))
                else:
                    raise ValueError("Salt length must be between 0 and 32 not: %d" %saltLength)
            else:
                raise TypeError("Salt Length must be an Integer")
        else:
            raise TypeError("Password must be in ASCII")
        
        
    def SETDELAY(self,delay):
        self.firstCmd = False
        if isinstance(delay,(int)):
            if delay>=0 and delay <100: 
                return (self.__writeCmd((self.setDelayText %delay)),self.__readData(self.setDelayTextLen))
            else:
                raise ValueError("Delay must be between 0 and 99 not: %s" %delay)
        else:
            raise TypeError("delay must be an INT")
        

def DongleStatus(deviceId = ""):

    try:
        stick =sc_driver(deviceId=device)
        if stick:
            getlocked = stick.GETLOCKED()
            getlocked = getlocked[1].split(" ")
            id = stick.GETID()
            id = id[1].split(" ")
            cluster = stick.GETCLUSTER()
            cluster = cluster[1].split(" ")
            stick.close()
            return (id[0], cluster[0], getlocked[0], getlocked[1].strip())
        else:
            return("","","","")
    except:
        return("0","","","")

if __name__ == "__main__":

    if len(sys.argv) != 2:
        noDongles = 0
        print("List of connected devices:")
        for device in sc_driver().getDeviceList():
            noDongles += 1
            (id, cluster, locked, counter) = DongleStatus(device[1])
            if id=="0":
                print("%s\n    Device ID: %s; API STATUS: Can't open." %(device[0],device[1])) 
            else:
                print("%s\n    Device ID: %s; API STATUS: (ID: %s, CLUSTER: %s, COUNTER: %s, LOCKED: %s." %(device[0],device[1], id, cluster, counter, locked)) 

 
        print("\n") 
        if noDongles <1:
            print("No Password S-CRIB found.") 
        else: 
            print("Please use the device ID if you want to open a particular device")
            print("Can call this script with a device ID as \ncommand line argument to get status information.")
    else:
        device = sys.argv[1]
        device = device.zfill(8)

        (id, cluster, locked, counter) = DongleStatus(device)
        if id=="":
            print("Password S-CRIB, ID=%s was not found"%device)
        else:
            print("%s %s %s %s %s"%(device, id, cluster, counter, locked)) 
            print("Password S-CRIB %s"%device)
            print("    API ID: %s"%id)
            print("    Cluster ID: %s"%cluster)
            print("    Operation counter: %s"%counter)
            if locked=="1":
                print("    It's in OPERATIONAL state (initialisation closed, GETLOCKED=%s)."%locked)
            else:
                print("    It's in INITIALISATION state (GETLOCKED=%s)."%locked)
        
    
