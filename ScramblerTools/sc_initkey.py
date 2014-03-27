#!/usr/bin/python
"""sc_initkey.py: utility script forS-CRIB Scramble device to format initialisation key 
it requires input string of 40 hex characters - project sCribManager - Python."""

'''
@author: Dan Cvrcek 
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''

import hashlib
import sys
import binascii

if __name__ == "__main__":
    args = len(sys.argv)-1
    if args==1:
        data = sys.argv[1]
        bindata = binascii.unhexlify(data) 
        hash_obj = hashlib.sha1()
        hash_obj.update(bindata)
        crc = hash_obj.hexdigest()[:4]
        prefix = ''
	byte1 = ord(bindata[1])
	for i in range(4):
	   prefix = chr(0x31+(byte1&0x3)) + prefix
	   byte1 = byte1 / 4
        byte0 = ord(bindata[0])
        for i in range(4):
            prefix = chr(0x31+(byte0&0x3)) + prefix
            byte0 = byte0 / 4

        initkey0 = prefix + data[4:] + crc
        initkey1 = initkey0.upper()
        print(initkey1) 
    else:
        print("This script must be callled with exactly one argument - 40 characters long hex string")

