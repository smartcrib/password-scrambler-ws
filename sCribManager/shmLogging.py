#!/usr/bin/python

"""shmLogging.py: a simple module that opens loggers for the process
   project S-CribManager - Python."""

'''
@author: Dan Cvrcek, George French
@copyright: Copyright 2013-14, Smart Crib Ltd
@credits: George French, Dan Cvrcek
@license: GPL version 3 (e.g., https://www.gnu.org/copyleft/gpl.html)
@version: 1.0
@email: info@s-crib.com
@status: Test
'''
import logging
import logging.config
import socket
import platform
import json

_version = "1.0"
_patchlevel = "0"
_processID = "SHM"




class StructuredMessage(object):
    def __init__(self, code, message, **kwargs):
        self.code = code
        self.kwargs = kwargs
        self.kwargs['patch'] = _patchlevel
        self.kwargs['desc'] = message

    def __str__(self):
        code = _processID+self.code
        return '"code": "%s", "version": "%s", "IP": "%s", "server": "%s", "details":%s' % (code, _version, myIPaddr, myName, json.dumps(self.kwargs))

class StructuredMessageUsage(object):
    def __init__(self, code, operation, user, source, **kwargs):
        self.code = code
        self.kwargs = kwargs
        self.kwargs['cmd'] = operation
        self.kwargs['source'] = source
        self.user = user

    def __str__(self):
        code = _processID+self.code
        return '"code": "%s", "user": "%s", "IP": "%s", "server": "%s", "details":%s' % (self.code, self.user, myIPaddr, myName, json.dumps(self.kwargs))

_T = StructuredMessage   # optional, to improve readability
_U = StructuredMessageUsage


def log_use(code, operation, user, source, **kwargs):
    logger_use.info(_U(code+"USE", operation, user, source, **kwargs))

def log_trace(level, code, message, **kwargs):
    if level=="I":
        logger_trace.info(_T(code+"INF", message, **kwargs))
    elif level=="D":
        logger_trace.debug(_T(code+"DBG", message, **kwargs))
    elif level=="W":
        logger_trace.warning(_T(code+"WRN", message, **kwargs))
    elif level=="E":
        logger_trace.error(_T(code+"ERR", message, **kwargs))
    elif level=="C":
        logger_trace.critical(_T(code+"CRI", message, **kwargs))
    else:
        logger_trace.error(_T('0038ERR', "Incorrect format of log event", level=level, code=code))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8",80))
myIPaddr = (s.getsockname()[0])
s.close()
myName = platform.uname()[1]

logging.config.fileConfig('logging.conf')
logger_use = logging.getLogger('scrambler.usage')
logger_trace = logging.getLogger('scrambler.trace')

