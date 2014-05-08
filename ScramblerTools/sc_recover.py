#!/usr/bin/python
"""sc_recover.py: utility script for S-CRIB Scramble device to push initialisation key 
to S-CRIB Scrambler device - project sCribManager - Python."""

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
            return (id[0], cluster[0], getlocked[0], counter)
        else:
            return("","","","")
    except:
        return("0","","","")


def InjectInitKey(deviceID = "", initKey =""):            
    try:
        stick =sc_driver(deviceId=deviceId)
        if stick:
            if (initKey != ""):
                try:
                    result = stick.SETINITKEY(initKey)
                except:
                    result = "ERR700 Error in this script"
            else:
                result = "ERR700 You have to supply initialisation key"
    except:
        result = "ERR700 Error in this script, please try again or check S-CRIB device and pylibftdi library"
    return result

if __name__ == "__main__":

    if len(sys.argv) != 3:
        noDongles = 0
        print("List of connected devices and their clusters:")
        for device in sc_driver().getDeviceList():
            noDongles += 1
            (id, cluster, locked, counter) = DongleStatus(device[1])
            if id=="0":
                print("%s\n    Device ID: %s; API STATUS: Can't open." %(device[0],device[1]))
            else:
                print("%s\n    Device ID: %s; API STATUS: (ID: %s, CLUSTER: %s, INIT KEY EXPORT: %s, COUNTER: %s." %(device[0],device[1], id, cluster, locked, counter))


        print("\n")
        if noDongles <1:
            print("No S-CRIB Scrambler found.")
        else:
            print("Please use the device ID to push new initialisation key to S-CRIB Scrambler.")
            print("Call this script with a device ID and init key as \ncommand line arguments to initialise an S-CRIB Scrambler device.")
    else:
        device = sys.argv[1]
        device = device.zfill(8)
        initKey = sys.argv[2]

        (id, cluster, locked, counter) = DongleStatus(device)
        if id=="":
            print("S-CRIB Scrambler, ID=%s was not found"%device)
        else:
            if locked == "0":
                result = InjectInitKey(device, initKey)
                print(result)
                print("S-CRIB Scrambler %s"%device)
                print("    API ID: %s"%id)
                print("    Cluster ID: %s"%cluster)
                print("    Operation counter: %s"%counter)
            else:
                print("ERR700")
                print("S-CRIB Scrambler's initialisation is disabled.\n")
                print("S-CRIB Scrambler %s"%device)
                print("    API ID: %s"%id)
                print("    Cluster ID: %s"%cluster)
                print("    Operation counter: %s"%counter)
                print("    Already in OPERATIONAL state (initialisation key export disabled, GETLOCKED=%s)."%locked)
        
