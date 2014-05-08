#!/usr/bin/python
"""sc_crypto.py: a class interfacing a physical S-CRIB Scramble device for command line 
utilities through pylibftdi library - project sCribManager - Python."""

'''
@author: Dan Cvrcek 
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''

import time
import binascii
import sys
import time
from Crypto.Cipher import AES

class sc_crypto(object):

    def __init__(self,deviceId=""):
        '''
        Constructor
        '''
#   Helper functions - cryptography
    BLOCK_SIZE = 16

    def encrypt(self, message, passphrase):
        """
        Test
        """
        # passphrase MUST be 16, 24 or 32 bytes long, how can I do that ?
        IV =  "\x00" * self.BLOCK_SIZE
        while (len(passphrase)<32):
            passphrase = passphrase + "\x00"

        aes = AES.new(passphrase, AES.MODE_CBC, IV)
        return aes.encrypt(message)


    def decrypt(self, encrypted, passphrase):
        IV = "\x00" * self.BLOCK_SIZE
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


if __name__ == "__main__":
    pass
