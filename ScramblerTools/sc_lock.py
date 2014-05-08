#!/usr/bin/python
"""sc_lock.py: utility script for S-CRIB Scrambler device to print communication key 
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
from sc_driver import sc_driver

def DongleLock(deviceId = ""):

    try:
        stick =sc_driver(deviceId=deviceId)
        if stick:
            id = stick.GETID()
            id = id[1].split(" ")
            cluster = stick.GETCLUSTER()
            cluster = cluster[1].split(" ")
	    counter = cluster[1].strip()
            locking = stick.SCRAMBLE("pwd",10)
            locked = stick.GETLOCKED()
	    locked = locked[1].split(" ")

            stick.close()
            return (id[0], cluster[0], counter, locked[0])
        else:
            return("","","","")
    except ValueError, e:
        print e
        return("0","","","")
    except TypeError, e:
        print e
        return("0","","","")

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

    if len(sys.argv) != 2:
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
            print("Please use the device ID to request its locking or 'ALL' to lock all dongles")
            print("Call this script with a device ID as \ncommand line argument to get a new communication key.")
    else:
        device = sys.argv[1]
        device_list = []
	if device == 'ALL':
            for one in sc_driver().getDeviceList():
                device_list.append(one[1])
	else:
            device = device.zfill(8)
            device_list.append(device)

	for device in device_list:
            (id, cluster, counter, locked) = DongleLock(device)
            if id=="":
                print("S-CRIB Scrambler, ID=%s was not found"%device)
            else:
                if locked =="1":
                    result = "SUCCESS"
                else:
                    result = "FAIL"
                print("%s %s %s %s %s %s"%(device, id, cluster, locked, counter, result))
                #print("S-CRIB Scrambler %s"%device)
                #print("    API ID: %s"%id)
                #print("    Cluster ID: %s"%cluster)
                #print("    Locked: %s"%locked)
                #print("    API Command Counter: %s"%counter)
        
