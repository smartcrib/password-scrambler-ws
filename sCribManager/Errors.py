#!/usr/bin/env python

"""Errors.py: Definition of error codes for sCribManager - Python."""

'''
@author: Dan Cvrcek, George French
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''

class Errors(object):
    '''
    classdocs
    '''
    ERR_OK = 0
    ERR_INTERNAL = 1
    ERR_REMOTE = 2
    ERR_ENCODING = 3
    ERR_LOWERCASE = 4
    ERR_RANGE = 5
    ERR_LENGTH = 6
    ERR_PARAMS = 7
    ERR_CMD = 8
    ERR_CRYPTO = 9
    ERR_INITKEYLEN = 101
    ERR_LOCKED = 102
    ERR_PWDINDEX = 103
    ERR_PWDINDEXSTR = 104
    ERR_SALTMISMATCH = 105
    ERR_SALTLEN = 106
    ERR_SALTLENSTR = 107
    ERR_PWDCHARS = 108
    ERR_DELAYVAL = 109
    ERR_DELAYSTR = 110
    ERR_SCRAMBLEPARAMS = 111
    ERR_COMMAND = 112
    ERR_COMMANDOTHER =113
    ERR_HARDWARE = 114
    ERR_NOHARDWARE = 115
    ERR_UNKNOWNCMD = 116
    ERR_SHUTDOWN = 117
    ERR_INTEGRITY = 118
    ERR_UNPLUGGED = 119
    ERR_INTEGRITY2 = 120
    ERR_DUPLICATEHW = 121
    ERR_NODEVICE = 122
    ERR_NOTOKEN = 123
    ERR_ADDRECORD_NONE = 124
    ERR_INVALIDDONGLE = 125
    ERR_QUEUETIMEOUT = 126
    ERR_COMMAND_CLUSTER = 127
    ERR_COMMANDOTHER_CLUSTER = 128
    ERR_COMMAND_NOTIMPLEMENTED = 129
    ERR_ENCRYPTEDBLOCK_LEN = 130
    ERR_ENGETID_ID = 131
    ERR_CLUSTER_OF_ONE_ONLY = 132

    ERR_PARAMHEX = 201
    ERR_REMOTE =202
    ERR_INTERNALFWD = 203
    ERR_INTERNALOTHER = 204
    ERR_INTERNALNORESP = 205
    ERR_APIKEYEXISTS = 206
    ERR_APIKEYNOTFOUND = 207

    ERR_SERVERCOUNTER = 301
    ERR_DECRYPT = 302
    
    ERR_EXCEPTION = 401
    ERR_MALFUNCTION = 402
    ERR_ENUMERATE = 403
    ERR_DRIVER = 404
    ERR_UNPLUGGED_ID = 405
    ERR_UNPLUGGED_CLUSTER = 406
    ERR_UNPLUGGED_ENUM = 407
    ERR_UNPLUGGED_OPEN = 408
    ERR_UNPLUGGED_READ = 409
    ERR_UNPLUGGED_WRITE = 410
    ERR_TIMEOUT_READ = 411
                     
    _errors = {
# HW errors
               ERR_OK:  {'code': "ERR000", 'log':"", 'desc':""},
               ERR_INTERNAL:  {'code': "ERR001", 'log':"", 'desc':""},
               ERR_REMOTE:  {'code': "ERR002", 'log':"", 'desc':""},
               ERR_ENCODING:  {'code': "ERR003", 'log':"", 'desc':""},
               ERR_LOWERCASE:  {'code': "ERR004", 'log':"", 'desc':""},
               ERR_RANGE:  {'code': "ERR005", 'log':"", 'desc':""},
               ERR_LENGTH:  {'code': "ERR006", 'log':"", 'desc':""},
               ERR_PARAMS:  {'code': "ERR007", 'log':"", 'desc':""},
               ERR_CMD:  {'code': "ERR008", 'log':"", 'desc':""},
               ERR_CRYPTO:  {'code': "ERR009", 'log':"", 'desc':""},
# driver errors
               ERR_EXCEPTION:  {'code': "ERR401", 'log':"", 'desc':""},
               ERR_MALFUNCTION:  {'code': "ERR402", 'log':"", 'desc':""},
               ERR_ENUMERATE:  {'code': "ERR403", 'log':"", 'desc':""},
               ERR_DRIVER:  {'code': "ERR404", 'log':"", 'desc':""},
               ERR_UNPLUGGED_ID:  {'code': "ERR405", 'log':"", 'desc':""},
               ERR_UNPLUGGED_CLUSTER:  {'code': "ERR406", 'log':"", 'desc':""},
               ERR_UNPLUGGED_ENUM: {'code': "ERR407", 'log':"", 'desc':""},
               ERR_UNPLUGGED_OPEN: {'code': "ERR408", 'log':"", 'desc':""},
               ERR_UNPLUGGED_READ: {'code': "ERR409", 'log':"", 'desc':""},
               ERR_UNPLUGGED_WRITE: {'code': "ERR410", 'log':"", 'desc':""},
               ERR_TIMEOUT_READ: {'code': "ERR411", 'log':"", 'desc':""},
               

# middleware errors
               ERR_INITKEYLEN:  {'code': "ERR101", 'log':"", 'desc':""},
               ERR_LOCKED:  {'code': "ERR102", 'log':"", 'desc':""},
               ERR_PWDINDEX:  {'code': "ERR103", 'log':"", 'desc':""},
               ERR_PWDINDEXSTR:  {'code': "ERR104", 'log':"", 'desc':""},
               ERR_SALTMISMATCH:  {'code': "ERR105", 'log':"", 'desc':""},
               ERR_SALTLEN:  {'code': "ERR106", 'log':"", 'desc':""},
               ERR_SALTLENSTR:  {'code': "ERR107", 'log':"", 'desc':""},
               ERR_PWDCHARS:  {'code': "ERR108", 'log':"", 'desc':""},
               ERR_DELAYVAL:  {'code': "ERR109", 'log':"", 'desc':""},
               ERR_DELAYSTR:  {'code': "ERR110", 'log':"", 'desc':""},
               ERR_SCRAMBLEPARAMS:  {'code': "ERR111", 'log':"", 'desc':""},
               ERR_COMMAND:  {'code': "ERR112", 'log':"", 'desc':""},
               ERR_COMMANDOTHER:  {'code': "ERR113", 'log':"", 'desc':""},
               ERR_HARDWARE:  {'code': "ERR114", 'log':"", 'desc':""},
               ERR_NOHARDWARE:  {'code': "ERR115", 'log':"", 'desc':""},
               ERR_UNKNOWNCMD:  {'code': "ERR116", 'log':"", 'desc':""},
               ERR_SHUTDOWN:  {'code': "ERR117", 'log':"", 'desc':""},
               ERR_INTEGRITY: {'code': "ERR118", 'log':"", 'desc':""},
               ERR_UNPLUGGED: {'code': "ERR119", 'log':"", 'desc':""},
               ERR_INTEGRITY2: {'code': "ERR120", 'log':"", 'desc':""},
               ERR_DUPLICATEHW: {'code': "ERR121", 'log':"", 'desc':""},
               ERR_NOTOKEN: {'code': "ERR122", 'log':"", 'desc':""},
               ERR_NODEVICE: {'code': "ERR123", 'log':"", 'desc':""},
               ERR_ADDRECORD_NONE: {'code': "ERR124", 'log':"", 'desc':""},
               ERR_INVALIDDONGLE: {'code': "ERR125", 'log':"", 'desc':""},
               ERR_QUEUETIMEOUT:  {'code': "ERR126", 'log':"", 'desc':""},
               ERR_COMMAND_CLUSTER:  {'code': "ERR127", 'log':"", 'desc':""},
               ERR_COMMANDOTHER_CLUSTER:  {'code': "ERR128", 'log':"", 'desc':""},
               ERR_COMMAND_NOTIMPLEMENTED:  {'code': "ERR129", 'log':"", 'desc':""},
               ERR_ENCRYPTEDBLOCK_LEN:  {'code': "ERR130", 'log':"", 'desc':""},
               ERR_ENGETID_ID:  {'code': "ERR131", 'log':"", 'desc':""},
               ERR_CLUSTER_OF_ONE_ONLY:  {'code': "ERR132", 'log':"", 'desc':""},
               
# API errors
               ERR_PARAMHEX:  {'code': "ERR201", 'log':"", 'desc':""},
               ERR_REMOTE:  {'code': "ERR202", 'log':"", 'desc':""},
               ERR_INTERNALFWD:  {'code': "ERR203", 'log':"", 'desc':""},
               ERR_INTERNALOTHER:  {'code': "ERR204", 'log':"", 'desc':""},
               ERR_INTERNALNORESP:  {'code': "ERR205", 'log':"", 'desc':""},
               ERR_APIKEYEXISTS: {'code': "ERR206", 'log':"", 'desc':""},
               ERR_APIKEYNOTFOUND: {'code': "ERR207", 'log':"", 'desc':""},
               
# client errors
               ERR_SERVERCOUNTER:  {'code': "ERR301", 'log':"", 'desc':""},
               ERR_DECRYPT:  {'code': "ERR302", 'log':"", 'desc':""},
    }

    def __init__(self, params):
        '''
        Constructor
        '''
        pass
 
