password-scrambler-ws
=====================

If you never heard about S-CRIB Scrambler, have a look at the project page at *http://docs.s-crib.com/doku.php/how_to_use_scramble_scrib*

Python implementation of a web service for Smart Crib hardware password scramblers

This implementation has been tested with Raspberry Pi with Raspbian. Monit scripts have not been tested in any way.

We hope to be able to provide image for Rasbian but here is a list of steps we completed to get the Scrambling service working.

Preparing Raspberry Pi
======================

0. Get an SD card (4GB or more), install Raspbian as suggested here (http://www.raspbian.org/RaspbianInstaller) and make sure you can ssh to your Raspberry Pi.
1. setting off:
   - create user scrib: sudo adduser scrib
   - change the default "raspberry" password for 'pi' user
2. install svn: sudo apt-get install subversion
3. install ufw firewall
    sudo apt-get install ufw   # warning -  warning: script 'mathkernel' missing LSB tags and overrides
4. setup firewall so yo don't get locked out
    sudo apt-get install -y screen  
    sudo screen -S firewall
    while true; do sudo ufw allow from 192.168.1.0/24; ufw enable --forse-enable; sleep 60; done
    detach with ctrl+a d
5. setup firewall ports
    sudo ufw allow 22
    sudo ufw allow from 192.168.1.0/24  #not strictly necessary - allows unlimited access from LAN
    sudo ufw allow 4242  #port for the Web Service
    sudo ufw status  #check the rules have been applied
    sudo ufw --force enable
6. get the web service code
    sudo su scrib
    cd /home/scrib
    svn checkout https://github.com/smartcrib/password-scrambler-ws/trunk/sCribManager .
    exit  #back from user scrib to user pi
7. copy init files to the system directory
    sudo cp /home/scrib/misc/scribmanager /etc/init.d/
    sudo cp /home/scrib/misc/scribrestfull /etc/init.d/
8. update privileges on these files
    sudo chmod 755 /etc/init.d/scribmanager
    sudo chmod 755 /etc/init.d/scribrestfull
9. make 2 main Python scripts executable as well
    sudo chmod 755 /home/scrib/scribTCPServer.py
    sudo chmod 755 /home/scrib/scribREST.py
10. install some more tools
    sudo apt-get install python-pip
    sudo apt-get install python-ftdi  #http://code.google.com/p/drcontrol/wiki/Install_RaspberryPi
    sudo pip install pylibftdi
11. Update a configuration file for FTDI devices
    sudo vi /etc/udev/rules.d/99-libftdi.rules
    ... and copy the following line to the file and save it with (ESC, :q <ENTER>)
# FTDI Devices: FT232BM/L/Q, FT245BM/L/Q, FT232RL/Q, FT245RL/Q, VNC1L with VDPS Firmware
SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0664", GROUP="plugdev"
12. update udev immediately:
    sudo udevadm trigger 'applies the new rule immediately even on plugged devices
13. add user 'scrib' to plugdev group so that it can read and write to Scramblers
    sudo adduser scrib plugdev
14. now we need to install all Python dependences:
    sudo apt-get install python-crypto
    sudo apt-get install   
    sudo apt-get install python-dev
    sudo pip install gevent
    sudo pip install bottle
15. also register the initialisation scripts so they are run after boot automatically
    sudo update-rc.d scribrestfull defaults
    sudo update-rc.d scribmanager defaults
    sudo update-rc.d scribrestfull enable
    sudo update-rc.d scribmanager enable
16. now you can start the service manually:
    sudo /etc/init.d/scribrestfull start
    sudo /etc/init.d/scribmanager start

Enabling HTTPS
==============
17. Install a web server that supports HTTPS
    sudo apt-get install python-cherrypy3 
18. Install OpenSSL for Python
    sudo apt-get install python-openssl
19. Create a certificate and a private key - the command will ask you for some details - we show input for our test
    sudo openssl req -new -x509 -keyout scrambler.pem -out scrambler.pem -days 3650 -nodes
      Country Name (2 letter code) [AU]:GB
      State or Province Name (full name) [Some-State]:Cambridgesire
      Locality Name (eg, city) []:Cambridge
      Organization Name (eg, company) [Internet Widgits Pty Ltd]:Smart Crib Ltd
      Organizational Unit Name (eg, section) []:S-CRIB Scrambler
      Common Name (e.g. server FQDN or YOUR name) []:scrambler.s-crib.com
      Email Address []:info@s-crib.com
    make sure the owner and privileges on the scrambler.pem file are correct
      sudo chown scrib:scrib scrambler.pem
      sudo chmod 0400 scrambler.pem
20. Open scribREST.py, find _ENABLE_SSL and set it to True
21. Try to restart the service, alternatively reboot the host computer

NOTE: Python would not verify certificate by default. It is necessary to correctly handle HTTPS connections and at least verify the hostname. We will amend documentation with this issue shortly.


Initial Configuration of Scramblers
===================================


