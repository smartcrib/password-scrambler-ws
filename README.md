password-scrambler-ws
=====================

If you never heard about S-CRIB Scrambler, have a look at the project page at *http://docs.s-crib.com/doku.php/how_to_use_scramble_scrib*

Python implementation of a web service for Smart Crib hardware password scramblers

This implementation has been tested on Raspberry Pi with Raspbian. Monit scripts have not been tested in any way and they are work-in-progress.

We hope to be able to provide image for Rasbian but here is a list of steps we completed to get the Scrambling service working.

**When you plug Scrambler to Raspberry Pi, it will cause reset of Raspberry Pi. You may find it useful to plug your Scrambler to a USB hub with own power supply. Alternatively, plug your Scrambler to a Raspberry Pi and leave it there while you use it.** 

Preparing Raspberry Pi
======================

1. Get an SD card (4GB or more), install Raspbian as suggested here (http://www.raspbian.org/RaspbianInstaller) and make sure you can ssh to your Raspberry Pi.
2. Once your Raspberry is connected to the internet, Run **sudo rpi-update** and **sudo apt-get update && sudo apt-get upgrade**. Reboot when finished - **sudo shutdown -r now**.
3. setting off:
   - create user scrib: **sudo adduser scrib**
   - create user www-scrib: **sudo adduser www-scrib**
   - change the default "raspberry" password for 'pi' user: **passwd**
4. install svn: **sudo apt-get install subversion**
5. install ufw firewall
   - **sudo apt-get install ufw**   # warning -  warning: script 'mathkernel' missing LSB tags and overrides
6. setup firewall so yo don't get locked out
   - **sudo apt-get install -y screen**  
   - **sudo screen -S firewall**
   - **while true; do sudo ufw allow from 192.168.1.0/24; ufw enable --force-enable; sleep 60; done**
   - detach with ctrl+a d
7. setup firewall ports
    - **sudo ufw allow 22**
    - **sudo ufw allow from 192.168.1.0/24**  #not strictly necessary - allows unlimited access from LAN
    - **sudo ufw allow 4242**  #port for the Web Service - the same as set in scribREST.py
    - **sudo ufw status**  #check the rules have been applied
    - **sudo ufw --force enable**
8. get the web service code
    - **sudo su scrib**
    - **cd /home/scrib**
    - **svn checkout https://github.com/smartcrib/password-scrambler-ws/trunk/sCribManager .**
    - **exit**  #back from user scrib to user pi
9. copy init files to the system directory
    - **sudo cp /home/scrib/misc/scribmanager /etc/init.d/**
    - **sudo cp /home/scrib/misc/scribrestfull /etc/init.d/**
10. update privileges on these files
    - **sudo chmod 755 /etc/init.d/scribmanager**
    - **sudo chmod 755 /etc/init.d/scribrestfull**
11. to change default settings, open file scribREST.py and edit it; see below how to enable HTTPS
12. make 2 main Python scripts executable as well
    - **sudo chmod 755 /home/scrib/scribTCP.py**
    - **sudo chmod 755 /home/scrib/scribREST.py**
13. install some more tools
    - **sudo apt-get install python-pip**
    - **sudo apt-get install python-ftdi**  #http://code.google.com/p/drcontrol/wiki/Install_RaspberryPi
    - **sudo pip install pylibftdi**
14. Update a configuration file for FTDI devices
    - **sudo vi /etc/udev/rules.d/99-libftdi.rules**
    ... and copy the following line to the file and save it with (ESC, :q <ENTER>)
    - *# FTDI Devices: FT232BM/L/Q, FT245BM/L/Q, FT232RL/Q, FT245RL/Q, VNC1L with VDPS Firmware*
    - *SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", MODE="0664", GROUP="plugdev"*
15. update udev immediately:
    - **sudo udevadm trigger** #applies the new rule immediately even on plugged devices
16. add user 'scrib' to plugdev group so that it can read and write to Scramblers
    - **sudo adduser scrib plugdev**
17. you can now test functionality of your S-CRIB Scrambler - see steps at the bottom of this manual
18. now we need to install all Python dependences:
    - **sudo apt-get install python-crypto**
    - **sudo apt-get install python-dev**
    - **sudo pip install gevent**  #this command will take a little while and cause quite a few warnings, be patient and ignore warnings so long as the command succeeds
    - **sudo pip install bottle**
19. also register the initialisation scripts so they are run after boot automatically
    - **sudo update-rc.d scribrestfull defaults**
    - **sudo update-rc.d scribmanager defaults**
    - **sudo update-rc.d scribrestfull enable**
    - **sudo update-rc.d scribmanager enable**
20. now you can start the service manually:
    - **sudo /etc/init.d/scribrestfull start**
    - **sudo /etc/init.d/scribmanager start**
21. at the end you can uninstall python-dev as it is not needed any more: **sudo apt-get remove python-dev**

Enabling HTTPS
==============
22. Install a web server that supports HTTPS
    - **sudo apt-get install python-cherrypy3**
23. Install OpenSSL for Python
    - **sudo apt-get install python-openssl**
24. Create a certificate and a private key - the command will ask you for some details - we show input for our test
    - **sudo openssl req -new -x509 -keyout scrambler.pem -out scrambler.pem -days 3650 -nodes**
    -   Country Name (2 letter code) [AU]:GB
    -   State or Province Name (full name) [Some-State]:Cambridgesire
    -   Locality Name (eg, city) []:Cambridge
    -   Organization Name (eg, company) [Internet Widgits Pty Ltd]:Smart Crib Ltd
    -   Organizational Unit Name (eg, section) []:S-CRIB Scrambler
    -   Common Name (e.g. server FQDN or YOUR name) []:scrambler.s-crib.com
    -   Email Address []:info@s-crib.com
    - make sure the owner and privileges on the scrambler.pem file are correct
    - **sudo chown scrib:scrib scrambler.pem** #when you change the file name, update the scribREST.py file as well
    - **sudo chmod 0400 scrambler.pem**
25. Open scribREST.py, find _ENABLE_SSL and set it to True
26. Try to restart the service, alternatively reboot the host computer

NOTE: Python would not verify certificate by default. It is necessary to correctly handle HTTPS connections and at least verify the hostname. We will amend documentation with this issue shortly.


Testing Functionality of Scrambler(s)
====================================

27. change effective user to scrib: **sudo su scrib**
28. create a folder for Scrambler tools - **mkdir /home/scrib/tools**; go to the new folder **cd /home/scrib/tools**
29. upload tools from GitHub: ** svn checkout https://github.com/smartcrib/password-scrambler-ws/trunk/ScramblerTools .**
30. if your Scrambler is plugged to the Raspberry, run **python sc_driver.py**; you should see status information about the Scrambler, something like:
   - List of connected devices:
   - Smart Crib:Scrambler:00000000
   -    Device ID: 00000000; API STATUS: (ID: 0102030000000000, CLUSTER: 8mxaN*_d13, COUNTER: 00000001, LOCKED: 1.




Initial Configuration of Scramblers
===================================

The ScramblerTools folder contains several scripts that you will need for initial configuration.

 - **sc_backup.py** - lists the plugged Scramblers and also prints initialisation key when a Scrambler ID is typed as a command line parameter
 - **sc_pwd4.py** - prints communication key for a selected dongle

Use the first script to create and print a backup for a new dongle. The second script prints a communication key that has to be entered to the client that will use the dongle.

Dongles are pre-initialised. You can reset them so that they would generate a new random initialisation key. You press the following combination of keys to reset a Scrambler:
 - press and hold all 4 buttons until the Blue LED shows
 - press and hold buttons 3 and 4 (closest to the computer) until the Green LED shows
 - press the Green button.

The Scrambler will switch both LEDs off in a few (less than 5 seconds). If it does not work, unplug and plug the dongle and try again.

When you unplug and plug the reset Scrambler again, you need to send it some data so that the Scrambler can start collecting timing information. You can use any serial terminal to do that and we will add a python script **sc_reset.py** to help with this shortly. The Scrambler will switch the Green LED on and type "OK" when the reset/initialisation is completed.

You have two options: you will use the initialisation key generated by the dongle and back it up as described above.

The second option is that you generate your own initialisation key. You need to follow steps:
 - create a random string of 160 bits and format it into a hex string - 40 characters
 - use the **sc_initkey.py** script to re-format the random string into an initialisation key
 - use the **sc_recover.py** to push the initialisation key into the dongle.

In both cases you should create a backup of the dongle with **sc_backup.py** and you will need the communication key that you can get with the **sc_pwd4.py** script.

Enroling Scramblers to Web Service
==================================

The web service now offers several API commands that allow you to create API key for new Scramblers and enrol them to the web service.

 - **http://localhost:4242/ADDAPICLIENT/<scramblerID>** will return an API key for a dongle with the 10 character <scramblerID> identification. (Use https if you configured SSL.)
 - Any time, you can query the web service for the API ID using **http://localhost:4242/CHECKAPICLIENT/<scramblerID>**.

You do not have to restart the webservice. You can simply plug the Scrambler to the host and start using it once the ADDAPICLIENT command has been successfully completed.

Cloning Scramblers
==================

You need to create an account at https://my.s-crib.com to create initialisation keys for cloning.

The online system is straightforward to use. You will need serial numbers of source and destination Scrambler (use the GETID command to obtain it or the output of *sc_backup.py*).

Once you have the cloning initialisation key, you can simply push it into the new Scrambler with the *sc_recover.py* script.
