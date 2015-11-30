#!/usr/bin/env python3
######################
### Kevin Mittman ####
######################
import os, sys
import socket

def goodbye():
	print("\nExiting...")

def authorize(sock):
	reply(sock, "\n220 FTP Server ready...")
	username = getReply(sock)
	if username == "anonymous":
		reply(sock, "\n230 Guest login ok, access restrictions apply.")
	else:
		reply(sock, "\n331 Password required for " + username)
		password = getReply(sock)
		try:
			i = users.index(username)
		except ValueError:
			return 1

		try:
			pwds[i]
		except IndexError:
			return 1

		response = "\n230 User " + username + " logged in.\n"
		response += "Remote system type is " + sys.platform + "."
		reply(sock, response)

def reply(sock, msg):
	msgLen = str(len(msg))

	while len(msgLen) < 40:
		msgLen = "0" + msgLen

	msg = msgLen + msg
	numSent = 0
	while len(msg) > numSent:
		numSent += sock.send(bytes(msg[numSent:], 'UTF-8'))

	## Close the socket and the file
	sock.close()

def getReply(sock):
	# Accept connections
	clientSock, addr = sock.accept()
	ipv4 = addr[0]
	port = addr[1]
	#print("Accepted connection from client: " + str(ipv4) + ":" + str(port) + "\n")

	# The buffer to all data received from the client
	msgData = ""
	# The temporary buffer to store the received data
	recvBuff = ""
	# The size of the incoming file
	msgSize = 0	
	# The buffer containing the file size
	msgSizeBuff = ""

	replyBuff = retrieve(clientSock, 40)
	replyBin = retrieve(clientSock, int(replyBuff))
	reply = str(replyBin.decode('UTF-8'))

	clientSock.shutdown(socket.SHUT_RDWR) 
	clientSock.close()
	return reply

def connect(hostname, port):
	# Create a TCP socket
	downSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	downSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# Connect to the server
	try:
		downSock.connect((hostname, port))
	except ConnectionRefusedError:
		print("10061 Connection refused")
		return 1

	return downSock

def cd(sock, path=None):
	response = "200 Port command successful"
	try:
		os.chdir(path)
		print("<Server> cd " + 	os.getcwd())
		response += "\n250 CWD command successful"
		reply(sock, response)
	except FileNotFoundError:
		response += "\n550 Directory unavailable"
		reply(sock, response)
	sock.close()

def ls(sock, path=None):
	print("<Client> ls " + str(path))
	response = "200 Port command successful\n"
	response += "150 Opening data channel for directory list\n"

	try:
		result = [os.curdir, os.pardir] + os.listdir(path)
		response += "\n".join(result) + '\n\n'
		response += "226 Transfer ok."
		reply(sock, response)
		sock.close()
		return 0
	except FileNotFoundError:
		response += "550 No such file"
		reply(sock, response)
		sock.close()
		return 1
	except NotADirectoryError:
		response += "550 No such directory"
		reply(sock, response)
		sock.close()
		return 1

def listen(socket, port):
	# Bind the socket to the port
	try:
		ftpSock.bind(('', port))
	except PermissionError:
		print("Ports below 1024 require root permission!")
		return 1
	except OSError:
		print("Port already in use. Try again")
		return 1

	# Start listening on the socket
	ftpSock.listen(1)
	return 0

def ephemeral():
	# Create a socket
	tmpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tmpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# Bind the socket to first available port 
	tmpSocket.bind(('', 0))
	# Retreive the ephemeral port number
	tmpPort = tmpSocket.getsockname()[1]
	# Start listening on the socket
	tmpSocket.listen(1)

	return tmpSocket, tmpPort

def put(replySock, fileName):
	tmpSocket, tmpPort = ephemeral()

	# Accept connections forever
	print("Waiting for " + fileName + " on port " + str(tmpPort) + "...")
	reply(replySock, str(tmpPort))

	# Accept connections
	clientSock, addr = tmpSocket.accept()
	ipv4 = addr[0]
	port = addr[1]
	print("Receiving file from client: " + str(ipv4) + ":" + str(port) + "\n")

	# Receive the first 10 bytes indicating the size of the file
	fileSizeBuff = retrieve(clientSock, 10)
	# Get the file size
	fileSize = int(fileSizeBuff)
	print("<Server> The file size is " + str(fileSize) + " bytes")
	# Get the file data
	fileData = retrieve(clientSock, fileSize)
	#print("The file data is:\n" + str(fileData.decode('UTF-8')))

	# Check if file exists
	try:
		with open(os.getcwd() + "/" + fileName) as test:
			fileName = fileName + ".new"
	except IOError:
		pass

	# Write to new file
	try:
		f = open(os.getcwd() + "/" + fileName, "w")
		f.write(str(fileData.decode('UTF-8')))
		f.close()
		print("<Server> Stored: " + os.getcwd() + "/" + fileName)
	except IOError as err:
		print(err.errno)
		print(err.strerror)

	# Close our side
	clientSock.shutdown(socket.SHUT_RDWR) 
	clientSock.close()

	response = "226 Transfer complete.\n" + fileName
	return response


# ************************************************
# Receives the specified number of bytes
# from the specified socket
# @param sock - the socket from which to receive
# @param numBytes - the number of bytes to receive
# @return - the bytes received
# *************************************************
def retrieve(sock, numBytes):
	# The buffer
	recvBuff = bytes("", 'UTF-8')

	# The temporary buffer
	tmpBuff = bytes("", 'UTF-8')

	# Keep receiving till all is received
	while len(recvBuff) < numBytes:
		# Attempt to receive bytes
		try:
			tmpBuff = sock.recv(numBytes)
		except ConnectionResetError:
			print("\n10054 Connection reset by peer")
			return 1
			

		# The other side has closed the socket
		if not tmpBuff:
			break

		# Add the received bytes to the buffer
		recvBuff += tmpBuff

	return recvBuff

def get(ftpSock, fileName):
	# The number of bytes sent
	numSent = 0
	# The file data
	fileData = None
	# Open the file
	fileObj = open(fileName, "r")

	# Keep sending until all is sent
	while True:
		fileSize = os.path.getsize(fileName)
		fileData = fileObj.read(fileSize)
	
		# Make sure we did not hit EOF
		if fileData:
			# Get the size of the data read and convert it to string
			dataSizeStr = str(len(fileData))
		
			# Prepend 0's to the size string until the size is 10 bytes
			while len(dataSizeStr) < 10:
				dataSizeStr = "0" + dataSizeStr
	
			# Prepend the size of the data to the file data.
			fileData = dataSizeStr + fileData	
		
			# The number of bytes sent
			numSent = 0
		
			# Send the data
			while len(fileData) > numSent:
				numSent += ftpSock.send(bytes(fileData[numSent:], 'UTF-8'))
	
		# The file has been read. We are done
		else:
			break
	
	# Close the socket and the file
	ftpSock.close()
	fileObj.close()
	return numSent

def daemon(ftpSock, port):
	# Accept connections forever
	print("Waiting for connections on port " + str(port) + "...")

	while True:
		# Accept connections
		clientSock, addr = ftpSock.accept()
		ipv4 = addr[0]
		port = addr[1]
		print("Accepted connection from client: " + str(ipv4) + ":" + str(port) + "\n")
		#authorize(ftpSock)

		loop = True
		while loop:
			# The buffer to all data received from the client
			fileData = ""
			# The temporary buffer to store the received data
			recvBuff = ""
			# The size of the incoming file
			fileSize = 0	
			# The buffer containing the file size
			fileSizeBuff = ""

			cmdBuff = retrieve(clientSock, 40)
			cmdBin = retrieve(clientSock, int(cmdBuff))
			cmd = str(cmdBin.decode('UTF-8'))

			if cmd.split(' ')[1] == "cd":
					cmdPort = cmd.split(' ')[0]
					# Create a TCP socket
					replySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					replySock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					# Connect to the server
					try:
						replySock.connect((ipv4, int(cmdPort)))
						if len(cmd.split(' ')) > 2:
							cd(replySock, cmd.split(' ')[2])
						else:
							cd(replySock)
					except ConnectionRefusedError:
						print("10061 Connection refused")
	
			elif cmd.split(' ')[1] == "ls":
					cmdPort = cmd.split(' ')[0]
					# Create a TCP socket
					replySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					replySock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					# Connect to the server
					try:
						replySock.connect((ipv4, int(cmdPort)))
						if len(cmd.split(' ')) > 2:
							ls(replySock, cmd.split(' ')[2])
						else:
							ls(replySock)
					except ConnectionRefusedError:
						print("10061 Connection refused")

			elif cmd.split(' ')[1] == "put":
					cmdPort = cmd.split(' ')[0]
					# Create a TCP socket
					replySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					replySock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					# Connect to the server
					try:
						replySock.connect((ipv4, int(cmdPort)))
						# Receive file contents
						response = put(replySock, cmd.split(' ')[2])
						# Receive control signals
						replySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
						replySock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
						try:
							replySock.connect((ipv4, int(cmdPort)))
							reply(replySock, response)
						except ConnectionRefusedError:
							print("10061 Connection refused")

					except ConnectionRefusedError:
						print("10061 Connection refused")

			elif cmd.split(' ')[1] == "get":
					cmdPort = cmd.split(' ')[0]

					# Create a TCP socket
					replySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
					replySock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
					# Connect to the server
					try:
						replySock.connect((ipv4, int(cmdPort)))
					except ConnectionRefusedError:
						print("10061 Connection refused")
						return 1
					# Send file name and port
					tmpSocket, tmpPort = ephemeral()
					fileName = cmd.split(' ')[2]
					baseName = os.path.basename(fileName)

					# Check if file exists
					try:
						with open(fileName) as test:
							print("Uploading " + fileName + "...")
							response = fileName + '\n' + baseName + '\n' + str(tmpPort)
							reply(replySock, response)
							# Remote port
							remotePort = getReply(tmpSocket)
							# Upload file contents
							status = connect(ipv4, int(remotePort))
							if status != 1:
								numSent = get(status, fileName)
								print("Sent " + str(numSent) + " bytes.")
					except IOError:
						print("Request for " + fileName + " failed")
						reply(replySock, "")

			elif cmd.split(' ')[1] == "quit":
				loop = False

		# Close our side
		clientSock.shutdown(socket.SHUT_RDWR) 
		clientSock.close()



# Credentials
users = [ "bob", "cathy", "daniel", "erica" ]
pwds = [ "12345", "meow", "password", "1991" ]

# The port on which to listen
port = 1234

if len(sys.argv) == 2:
	port = int(sys.argv[1])
elif len(sys.argv) > 2:
	print("USAGE: ./" + sys.argv[0] + "[port #]")

# Create a welcome socket. 
ftpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ftpSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
	# Note: ports below 1024 require root permission!
	if listen(ftpSock, port) == 0:
		daemon(ftpSock, port)
except KeyboardInterrupt:
	goodbye()
	try:
		sys.exit(1)
	except SystemExit:
		os._exit(1)

### END ###
