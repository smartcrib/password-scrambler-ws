#!/usr/bin/python
"""sc_backup.py: utility script for S-CRIB Scramble device to print initialisation key 
for backup - project sCribManager - Python."""

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

def DongleStatus(deviceId = "", getPwd = 0):

    try:
        stick =sc_driver(deviceId=device)
        if stick:
            getlocked = stick.GETLOCKED()
            getlocked = getlocked[1].split(" ")
            id = stick.GETID()
            id = id[1].split(" ")
            cluster = stick.GETCLUSTER()
            cluster = cluster[1].split(" ")
            counter = cluster[1].strip()
            if (getPwd != 0) and (getlocked[0] == "0"):
                try:
                    initkey = stick.GETINITKEY()
                    initkey = initkey[1].split(" ")
                    if len(initkey)>1:
                        counter = initkey[1].strip()
                except:
                    initkey = ("")
            else:
                initkey = ""
            stick.close()
            return (id[0], cluster[0], getlocked[0], counter,  initkey)
        else:
            return("","","","", "")
    except:
        return("0","","","", "")

if __name__ == "__main__":

    if len(sys.argv) != 2:
        noDongles = 0
        print("List of connected devices and their clusters:")
        for device in sc_driver().getDeviceList():
            noDongles += 1
            (id, cluster, locked, counter, _) = DongleStatus(device[1])
            if id=="0":
                print("%s\n    Device ID: %s; API STATUS: Can't open." %(device[0],device[1]))
            else:
                print("%s\n    Device ID: %s; API STATUS: (ID: %s, CLUSTER: %s, INIT KEY EXPORT: %s, COUNTER: %s." %(device[0],device[1], id, cluster, locked, counter))


        print("\n")
        if noDongles <1:
            print("No Password S-CRIB found.")
        else:
            print("Please use the device ID to request its initialisation key for backup.")
            print("Call this script with a device ID as \ncommand line argument to get initialisation key.")
    else:
        device = sys.argv[1]
        device = device.zfill(8)

        (id, cluster, locked, counter, initkey) = DongleStatus(device, 1)
        if id=="":
            print("Password S-CRIB, ID=%s was not found"%device)
        else:
            if locked == "0":
                print("%s %s %s %s %s %s"%(device, id, cluster, locked, counter, initkey))
                print("Please keep the following lines safe. We suggest to print the text and only")
                print("keep the hard copy!\n")
                print("Password S-CRIB %s"%device)
                print("    API ID: %s"%id)
                print("    Cluster ID: %s"%cluster)
                print("    Initialisation key: %s"%initkey)
                print("    Operation counter: %s"%counter)
            else:
                print("%s %s %s %s %s"%(device, id, cluster,locked, counter))
                print("    Already in OPERATIONAL state (initialisation key export disabled, GETLOCKED=%s)."%locked)
        
