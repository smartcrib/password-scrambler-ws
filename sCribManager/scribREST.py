#!/usr/bin/python

"""rest.py: a class accepts external requests in RESTful format:
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
from gevent import monkey;monkey.patch_all()
from gevent.pool import Pool
from bottle import route, run, request
import socket
import sys
import time

_HOST = 'localhost'
_PORT = 4241

def checkHexNumber(dongleid, length = None):
    #remove all spaces
    dongleid = dongleid.replace(" ","")
    try:
        int(dongleid, 16)
        if not length is None:
            dongleid = dongleid.zfill(length)
    except:
        raise ValueError("ERR201Dongle ID is not in valid format")

    return dongleid.upper()

def checkRemote(command, address):
    # limit access to commands to localhost only
    try:
        f=open("access.txt", 'a')
        f.write("From "+address+" at "+time.strftime("%d/%m/%Y")+" "+time.strftime("%H:%M:%S")+"\n")
        f.close()
    except:
        pass
    if (command == "ENGETID") or (command == "ENSCRAMBLE"):
        pass
    else:
        if (address!='localhost') and (address!="127.0.0.1"):
            pass
            # raise ValueError("ERR202Request not allowed from this client (%s)" %address)
        else:
            pass

def forwardRequest(request):
    sock = None
    received = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to server and send data
        sock.connect((_HOST, _PORT))
        sock.sendall(request)
        # Receive data from the server and shut down
        received = sock.recv(1024)
    except ValueError, e:
        if not sock is None:
            sock.close()
        print("Error when forwarding RESTful request (%s)"%e)
        return "ERR203"
    except:
        print("Unexpected error %s", sys.exc_info()[0])
        return "ERR204"
    sock.close()

    if received is None:
        return "ERR205"
    else:
        return received



@route('/GETID/<apikey>/<dongleid>')
def getID(apikey = '', dongleid = ''):
    command = "GETID"   
    try:
        checkRemote(command, request.remote_addr)
        dongleid = checkHexNumber(dongleid, 16)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + " " + dongleid + "\n")    
    return received


@route('/ENGETID/<apikey>/<encrypteddata>/<dongleID>')
def enGetID(apikey = '', encrypteddata = '', dongleID = ''):
    command = "ENGETID"
    try:
        checkRemote(command, request.remote_addr)
	encrypteddata = checkHexNumber(encrypteddata, 64)
	dongleID = checkHexNumber(dongleID, 16)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]
    received = forwardRequest(command + " " + apikey + " " + dongleID + " " + encrypteddata + "\n")    
    return received


@route('/ENSCRAMBLE/<apikey>/<encrypteddata>')
def enScramble(apikey = '', encrypteddata = ''):
    command = "ENSCRAMBLE"
    try:
        checkRemote(command, request.remote_addr)
        encrypteddata = checkHexNumber(encrypteddata, 128)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + " " + encrypteddata + "\n")    
    return received

@route('/GETCOUNTER/<apikey>/<dongleid>')
def getCounter(apikey = '', dongleid = ''):
    command = "GETCOUNTER"
    try:
        checkRemote(command, request.remote_addr)
        dongleid = checkHexNumber(dongleid, 16)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + " " + dongleid + "\n")    
    return received

@route('/GETCLUSTERCOUNTER/<apikey>')
def getClusterCounter(apikey = ''):
    command = "GETCLUSTERCOUNTER"
    try:
        checkRemote(command, request.remote_addr)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + "\n")    
    return received

@route('/GETINITKEY/<apikey>/<dongleid>')
def getInitKey(apikey = '', dongleid = ''):
    command = "GETINITKEY"
    try:
        checkRemote(command, request.remote_addr)
        dongleid = checkHexNumber(dongleid, 16)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + " " + dongleid + " " + "\n")    
    return received

@route('/GETPASSWD/<apikey>/<dongleid>/<passwordid>')
def getPasswd(apikey = '', dongleid = '', passwordid = ''):
    command = "GETPASSWD"
    try:
        checkRemote(command, request.remote_addr)
        dongleid = checkHexNumber(dongleid, 16)
        passwordid = passwordid.strip()
        int(passwordid, 10)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + " " + dongleid + " " + passwordid + "\n")    
    return received

@route('/GETCLUSTERDELAY/<apikey>')
def getClusterDelay(apikey = ''):
    command = "GETCLUSTERDELAY"
    try:
        checkRemote(command, request.remote_addr)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + "\n")    
    return received

@route('/SCRAMBLE/<apikey>/<password>/<saltlength>/<salt>')
@route('/SCRAMBLE/<apikey>/<password>/<saltlength>')
def scramble(apikey = '', password = '', saltlength = '', salt = None):
    command = "SCRAMBLE"
    try:
        checkRemote(command, request.remote_addr)
        password = password.strip()
        saltlength = saltlength.strip()
        int(saltlength, 10)
        saltlength = '%02d' % int(saltlength, 10)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]
    if salt is None:
        received = forwardRequest(command + " " + apikey + " " + password + " " + saltlength + "\n")    
    else:
        received = forwardRequest(command + " " + apikey + " " + password + " " + saltlength + " " + salt + "\n")    
    return received

@route('/GETCLUSTERID/<apikey>')
def getClusterID(apikey = ''):
    command = "GETCLUSTERID"
    try:
        checkRemote(command, request.remote_addr)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + "\n")    
    return received

@route('/GETCLUSTERLOCKED/<apikey>')
def isClusterLocked(apikey = ''):
    command = "GETCLUSTERLOCKED"
    try:
        checkRemote(command, request.remote_addr)
        apikey = apikey.strip()
    except ValueError,e:
        text = "%s"%e
        print(text[6:])
        return text[:6]

    received = forwardRequest(command + " " + apikey + "\n")    
    return received

# open definitions of sCribClients - apikeys and clusterIDs
Pool(20)
run(host="0.0.0.0", port=4242, reloader = 'True' ,server= 'gevent')
