#!/usr/bin/env python
"""helper.py: an example code for using command ENSCRAMBLE
    - project sCribManager - Python."""

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
import urllib2
#import sys


class Client(object):

    _BLOCK_SIZE = 16
    _READ_TIMEOUT = 2 # in seconds
    space = 1

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
        

    def ENSCRAMBLE(self,passphrase, serverCounter, password, saltLength=0, salt=""):
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
        if salt is None:
            salt = ""
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
	url = 'http://scrambler.s-crib.com:4242/ENSCRAMBLE/george/'+dataToSend
	print('URL with ENSCRAMBLE request: %s\n'%url)
	page = urllib2.urlopen(url)
	response = page.read().strip().split()
        print("Response from the server is:\n%s\n"%response)
        result = response[0].encode("ascii","ignore")
        # the result must be terminated with '\n'
	print result
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
        
    def ENGETID(self,passphrase, serverCounter, dongleID):
        # create the encrypted packet
        if len(serverCounter)>10:
            print("Server counter can be only 10 characters long - ENGETID")
            return "ERR109"
           
        if len(dongleID)>16:
            print("The dongle ID must be shorter than 17 characters")
            return "ERR131"
    
        try:
            dongleID = dongleID.strip().zfill(16)
            dongleIDbin = binascii.unhexlify(dongleID)
        except:
            print("The dongle ID must be a hexadecimal string")
            return "ERR131"

        message = serverCounter.ljust(10) + dongleIDbin

        padding = 32 - len(message)
        data = list(message+ "\x00"*padding)
        for i in range(32-padding, 32):
            data[i] = chr(padding)
    
        data = "".join(data)
        result = self._encrypt(data, passphrase)
        dataToSend = binascii.hexlify(result).upper()

        # call the dongle
	url = 'http://scrambler.s-crib.com:4242/ENGETID/george/'+dataToSend+'/'+dongleID
	print('URL with ENGETID request: %s\n'%url)
	page = urllib2.urlopen(url)
	response = page.read().strip().split()
        print("Response from the server is:\n%s\n"%response)
        result = response[0].encode("ascii","ignore")
        # the result must be terminated with '\n'
        data = binascii.unhexlify(result.strip())
        result = self._decrypt(data, passphrase)
        if (len(result)>0):
            if (serverCounter.ljust(10)!=result[:10]): #check the server challenge
                print("Server counter is incorrect IN: %s, OUT %s " % (serverCounter.ljust(10),result[:10]))
                return "ERR301"

            index = 10
            dongleIDback = binascii.hexlify(result[index:(index+8)]).upper()
            index += 8
            counter = (((ord(result[index])*256+ord(result[index+1]))*256+ord(result[index+2]))*256+ord(result[index+3]))
            return (dongleIDback, counter)
        else:
            print("No data returned")
            return "ERR302"
        
                
if __name__ == '__main__':
    transportKey = 'UfN3_EAy)C4e5Y0C/?/z/yPyYi7n-TFq'

    #create 10 character nonce on the server
    counterSecret = str(int(time.time()*10))[1:]
    password = "passw0rd"
    saltLength = 10
    salt = None
    print("We request scrambling of:\n  password: %s\n  with salt: %s\n  required salt length is: %d\n\n"%(password, salt, saltLength))
    client = Client()  
    start = time.time() 
    result = client.ENSCRAMBLE(transportKey, counterSecret, password, saltLength, salt)
    end = time.time()
    print("Result of ENSCRAMBLE command:\n  password: %s\n  salt: %s\n  server's counter is %d\n\n"%(result[0], result[1], result[2]))
    print("Latency is : %f\n\n"%(end-start)) 
       
    counterSecret = str(int(time.time()*10))[1:]
    dongleID = "0102030000000000"
    print("We request counter of:\n  dongle: %s\n\n"%(dongleID))
    start = time.time() 
    result = client.ENGETID(transportKey, counterSecret, dongleID)
    print result
    end = time.time()
    if len(result) > 1:
        print("Result of ENGETID command:\n  dongleID: %s\n  counter: %s\n\n"%(result[0], result[1]))
    else:
        print result
    print("Latency is : %f"%(end-start)) 




