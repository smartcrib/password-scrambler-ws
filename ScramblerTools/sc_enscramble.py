#!/usr/bin/python
"""sc_enscramble.py: utility script for S-CRIB Scrambler device to print communication key 
for use in Scrambler WS clients - project sCribManager - Python."""

'''
@author: Dan Cvrcek
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''

import sys
import binascii
from sc_driver import sc_driver
from sc_crypto import sc_crypto

def TestEnscramble(deviceId, pwd4, serverCounter, password, saltLength=0, salt=""):
    # create the encrypted packet
    if len(serverCounter)>10:
        raise ValueError("Server counter can be only 10 characters long")

    message = serverCounter.ljust(10)+" "+password.strip()+" "
    if not isinstance(saltLength, (int)):
        raise TypeError("salt length must be an INT")
    if saltLength<0 or saltLength > 16:
        raise ValueError("salt length must be between 0 and 16 not: %s" % saltLength)
    if (saltLength != len(salt)) and (len(salt)>0):
        raise ValueError("salt is not of expected length" % saltLength)

    message = message + "%02d"%saltLength
    if len(salt)>0:
        message = message +" "+salt

    padding = 64 - len(message)
    data = list(message+ "\x00"*padding)
    for i in range(64-padding, 64):
        data[i] = chr(padding)

    data = "".join(data)
    result = sc_crypto().encrypt(data, pwd4)
    dataToSend = binascii.hexlify(result).upper()

    # call the dongle
    try:
        stick = sc_driver(deviceId=deviceId)
	print("Packet ready for Scrambler - part: %s"% dataToSend[:48])
        if stick:
            (length, result) = stick.ENSCRAMBLE(dataToSend)
	    print("Response from Scrambler - part: %s"%result[:48])
            result = result.encode("ascii","ignore")
            # the result must be terminated with '\n'
            data = binascii.unhexlify(result.strip())
            result = sc_crypto().decrypt(data, pwd4)
            if (len(result)>0):
                if (serverCounter.ljust(11)!=result[:11]): #check the server challenge
                    raise ValueError("Server counter is incorrect IN: %s, OUT %s " % (serverCounter.ljust(10),result[:10]))

                index = 11
                password = binascii.hexlify(result[index:(index+20)]).upper()
                index += 20
                salt = result[index:(index+saltLength)]
                index += saltLength
                counter = (((ord(result[index])*256+ord(result[index+1]))*256+ord(result[index+2]))*256+ord(result[index+3]))
                return (password, salt, counter)
            else:
                return("", "", "")
        else:
            return("", "", "")
    except:
        return("","", "")

def DongleStatus(deviceId = ""):

    try:
        stick =sc_driver(deviceId=deviceId)
        if stick:
            getlocked = stick.GETLOCKED()
            getlocked = getlocked[1].split(" ")
            id = stick.GETID()
            id = id[1].split(" ")
            cluster = stick.GETCLUSTER()
            cluster = cluster[1].split(" ")
            counter = cluster[1].strip()
            stick.close()
            return (id[0], cluster[0], counter, getlocked[0])
        else:
            return("","","","")
    except:
        return("0","","","")


if __name__ == "__main__":

    if len(sys.argv) != 3:
        noDongles = 0
        print("List of connected devices and their clusters:")
        for device in sc_driver().getDeviceList():
            noDongles += 1
            (id, cluster,  counter, locked) = DongleStatus(device[1])
            if id=="0":
                print("%s\n    Device ID: %s; API STATUS: Can't open." %(device[0],device[1]))
            else:
                print("%s\n    Device ID: %s; API STATUS: (ID: %s, CLUSTER: %s, PWD EXPORT LOCK: %s, COUNTER: %s." %(device[0], device[1], id, cluster, locked, counter))


        print("\n")
        if noDongles <1:
            print("No S-CRIB Scrambler found.")
        else:
            print("Please use the 'device ID' and 'communication key (pwd4)' to test ENSCRAMBLE command.")
    else:
        device = sys.argv[1]
        device = device.zfill(8)
	pwd4 = sys.argv[2]

        (password, salt, counter) = TestEnscramble(device, pwd4, "00000007","password", 10)
        print("Scrambling of 'password', requesting salt of 10 characters:\n  pwd: %s, salt: %s, op. counter: %s\n\n"%(password, salt, counter))
        (password, salt, counter) = TestEnscramble(device, pwd4, "00000007","password", 10)
        print("Scrambling of 'password', requesting salt of 10 characters:\n  pwd: %s, salt: %s, op. counter: %s\n\n"%(password, salt, counter))
        (password, salt, counter) = TestEnscramble(device, pwd4, "00000007","password", 10, salt)
        print("Scrambling of 'password', supplying salt:\n  pwd: %s, salt: %s, op. counter: %s\n\n"%(password, salt, counter))


