#!/usr/bin/env python3
######################
### Kevin Mittman ####
######################
import os, sys
import getpass
import socket

def goodbye():
	print("\n221 Goodbye.")
	exit(0)

def authorize(sock):
	print(getReply(sock))
	username = input("Name (" + hostname + ":user): ")
	reply(sock, username)
	print(getReply(sock))
	if username == "anonymous":
		reply(sock, "")
	else:
		password = getpass.getpass("Password: ")
		reply(sock, password)
	print(getReply(sock))

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
	serverSock, addr = sock.accept()
	ipv4 = addr[0]
	port = addr[1]
	#print("Accepted connection from server: " + str(ipv4) + ":" + str(port) + "\n")

	# The buffer to all data received from the client
	msgData = ""
	# The temporary buffer to store the received data
	recvBuff = ""
	# The size of the incoming file
	msgSize = 0	
	# The buffer containing the file size
	msgSizeBuff = ""

	replyBuff = retrieve(serverSock, 40)
	replyBin = retrieve(serverSock, int(replyBuff))
	reply = str(replyBin.decode('UTF-8'))

	serverSock.shutdown(socket.SHUT_RDWR) 
	serverSock.close()
	return reply

def connect(hostname, port):
	# Create a TCP socket
	connSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	connSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	# Connect to the server
	try:
		connSock.connect((hostname, port))
	except ConnectionRefusedError:
		print("10061 Connection refused")
		return 1

	return connSock

def command(sock, cmd):
	cmdLen = str(len(cmd))

	while len(cmdLen) < 40:
		cmdLen = "0" + cmdLen

	cmd = cmdLen + cmd	
	numSent = 0
	while len(cmd) > numSent:
		numSent += sock.send(bytes(cmd[numSent:], 'UTF-8'))

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

def retrieve(sock, numBytes):
	# The buffer
	recvBuff = bytes("", 'UTF-8')

	# The temporary buffer
	tmpBuff = bytes("", 'UTF-8')

	# Keep receiving till all is received
	while len(recvBuff) < numBytes:
		# Attempt to receive bytes
		try:
			tmpBuff =  sock.recv(numBytes)
		except ConnectionResetError:
			print("\n10054 Connection reset by peer")
			return 1

		# The other side has closed the socket
		if not tmpBuff:
			break

		# Add the received bytes to the buffer
		recvBuff += tmpBuff

	return recvBuff

def put(ftpSock, fileName):
	print("150 Using binary mode data connection for " + fileName)

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

def get(replySock, fileName, baseName):
	tmpSocket, tmpPort = ephemeral()
	print("Waiting for " + baseName + " on port " + str(tmpPort) + "...")
	reply(replySock, str(tmpPort))

	# Accept connections
	serverSock, addr = tmpSocket.accept()
	ipv4 = addr[0]
	port = addr[1]
	print("Receiving file from server: " + str(ipv4) + ":" + str(port) + "\n")

	print("150 Using binary mode data connection for " + fileName + "\n")
	# Receive the first 10 bytes indicating the size of the file
	fileSizeBuff = retrieve(serverSock, 10)
	# Get the file size
	fileSize = int(fileSizeBuff)
	# Get the file data
	fileData = retrieve(serverSock, fileSize)
	#print("The file data is:\n" + str(fileData.decode('UTF-8')))

	# Check if file exists
	try:
		with open(os.getcwd() + "/" + baseName) as test:
			baseName += ".new"
	except IOError:
		pass

	# Write to new file
	try:
		f = open(os.getcwd() + "/" + baseName, "w")
		f.write(str(fileData.decode('UTF-8')))
		f.close()
		#print("<Client> Stored: " + os.getcwd() + "/" + baseName)
	except IOError as err:
		print(err.errno)
		print(err.strerror)

	# Close our side
	serverSock.shutdown(socket.SHUT_RDWR) 
	serverSock.close()

	print("226 Transfer complete.")
	print("remote: " + fileName + " local: " + baseName)
	print("Received " + str(os.path.getsize(fileName)) + " bytes.")

def interactive(sock):
	cmd = ""
	while cmd != "quit":
		cli = input("ftp> ")
		cmd = list(map(str, cli.split()))

		if cmd[0] == "help":
			print("Commands are:\n\n" + "cd\t" + "ls\t" + "get\t" + "put\t" + "quit") 
		elif cmd[0] == "cd":
			tmpSocket, tmpPort = ephemeral()
			cmd.insert(0, tmpPort)
			command(sock, ' '.join(str(e) for e in cmd))
			pwd = getReply(tmpSocket)
			print(pwd)

		elif cmd[0] == "ls":
			tmpSocket, tmpPort = ephemeral()
			cmd.insert(0, tmpPort)
			command(sock, ' '.join(str(e) for e in cmd))
			output = getReply(tmpSocket)
			print(output)

		elif cmd[0] == "put":
			fileName = cmd[1]
			# Check if file exists
			try:
				with open(fileName) as test:
					tmpSocket, tmpPort = ephemeral()
					cmd.insert(0, tmpPort)
					cmd[2] = os.path.basename(fileName)
					command(sock, ' '.join(str(e) for e in cmd))
					remotePort = getReply(tmpSocket)
					# Upload file contents
					status = connect(hostname, int(remotePort))
					if status != 1:
						numSent = put(status, fileName)
						response = getReply(tmpSocket)
						print("".join(response.split("\n")[:-1]))
						print("local: " + fileName + " remote: " + response.split("\n")[-1])
						print("Sent " + str(numSent) + " bytes.")
			except IOError:
				print("Upload of " + fileName + " failed")

		elif cmd[0] == "get":
			tmpSocket, tmpPort = ephemeral()
			cmd.insert(0, tmpPort)
			command(sock, ' '.join(str(e) for e in cmd))
			response = getReply(tmpSocket)
			if response == "":
				print("550 File not found")
			else:
				fileName = response.split("\n")[0]
				baseName = response.split("\n")[1]
				remotePort = response.split("\n")[2]
				# Create a TCP socket
				replySock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				replySock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				# Connect to the server
				try:
					replySock.connect((hostname, int(remotePort)))
					# Download file contents
					get(replySock, fileName, baseName)
				except ConnectionRefusedError:
					print("10061 Connection refused")
					return 1
				except OSError as e:
					if e.errno == 106:
						print("125 Already connected")
					else:
						print("ERROR " + str(e.errno))
						return 1

		elif cmd[0] == "quit":
			tmpSocket, tmpPort = ephemeral()
			cmd.insert(0, tmpPort)
			command(sock, ' '.join(str(e) for e in cmd))
			goodbye()

		else:
			print("\n502 Command not implemented.")



# Server address
hostname = "localhost"

# Server port
port = 1234

if len(sys.argv) == 3:
	hostname = str(sys.argv[1])
	port = int(sys.argv[2])
elif len(sys.argv) > 3:
	print("USAGE: ./" + sys.argv[0] + "[hostname] [port #]")

print("ftp> open\n(to) " + str(hostname) + ":" + str(port))
try:
	status = connect(hostname, port)
	if status != 1:
		print("Connected to " + hostname + ".")
		#authorize(status)
		interactive(status)
except KeyboardInterrupt:
	goodbye()
	try:
		sys.exit(1)
	except SystemExit:
		os._exit(1)

### END ###
