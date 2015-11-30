#!/usr/bin/env python3
###########################
### Kevin Mittman #########
###########################

import os, sys, subprocess

# The file name 
FILE_NAME = "codearray.h";

###########################################################
# Returns the hexidecimal dump of a particular binary file
# @execPath - the executable path
# @return - returns the hexidecimal string representing
# the bytes of the program. The string has format:
# byte1,byte2,byte3....byten,
# For example, 0x19,0x12,0x45,0xda,
##########################################################
def getHexDump(execPath):
	
	# The return value
	retVal = None
	
	# TODO:
	# 1. Use popen() in order to run hexdump and grab the hexadecimal bytes of the program.
	# 2. If hexdump ran successfully, return the string retrieved. Otherwise, return None.
	# The command for hexdump to return the list of bytes in the program in C++ byte format
	# the command is hexdump -v -e '"0x" 1/1 "%02X" ","' progName

	try:
		dump = subprocess.check_output(["/usr/bin/hexdump", "-v", "-e", '"0x" 1/1 "%02X" ","', execPath], stderr=subprocess.STDOUT)
		return dump
	except subprocess.CalledProcessError as ex:
		print(ex.returncode)
	except OSError:
		print("ERROR: cannot locate hexdump")

	return retVal


###################################################################
# Generates the header file containing an array of executable codes
# @param execList - the list of executables
# @param fileName - the header file to which to write data
###################################################################

def generateHeaderFile(execList, fileName):

	# The header file
	headerFile = None

	# The program array
	progNames = sys.argv

	# Open the header file
	headerFile = open(fileName, "w")

	# The program index
	progCount = 0

	# The lengths of programs
	progLens = []

	# Write the array name to the header file
	headerFile.write("#include <string>\n\nusing namespace std;\n\nunsigned char* codeArray[] = {");

	
	
	# TODO: for each program progName we should run getHexDump() and get the 
	# the string of bytes formatted according to C++ conventions. That is, each
	# byte of the program will be a two-digit hexadecimal value prefixed with 0x. 
	# For example, 0xab. Each such byte should be added to the array codeArray in 
	# the C++ header file. After this loop executes, the header file should contain 
	# an array of the following format:
	# 1. unsigned char* codeArray[] = {new char[<number of bytes in prog1>{prog1byte1, prog1byte2.....},
	# 				   new char[<number of bytes in prog2><{prog2byte1, progbyte2,....},
	#					........
	#				};
	for execPath in execList:
		bytes = getHexDump(execPath)
		byteSize = len(bytes)
		progLens.append(byteSize)

		if progCount > 0:
			headerFile.write("\t\t\t      ")

		headerFile.write("new unsigned char[" + str(byteSize) + "]{")

		strCount = 0
		string = bytes.decode('utf-8').split(',')
		strLength = len(string)
		for byte in string:
			if strCount == 0:
				pass
			elif strCount < strLength - 1:
				headerFile.write(", ")

			headerFile.write(byte)
			strCount = strCount + 1

		if progCount == len(execList) - 1:
			headerFile.write("}\n")
		else:
			headerFile.write("},\n")

		progCount = progCount + 1
	
	headerFile.write("};")


	# Add array to containing program lengths to the header file
	headerFile.write("\n\nunsigned int programLengths[] = {")

	# The number of programs
	numProgs = 0 
	
	# TODO: add to the array in the header file the sizes of each program.
	# That is the first element is the size of program 1, the second element
	# is the size of program 2, etc.
	for progName in execList:
		fileSize = os.path.getsize(progName)
		if numProgs != 0:
			headerFile.write(", ")

		headerFile.write(str(fileSize))
		numProgs = numProgs + 1
	headerFile.write("};")

	
	# TODO: Write the number of programs.
	headerFile.write("\n\n#define NUM_BINARIES " +  str(len(progNames) - 1))
	
	# Close the header file
	headerFile.close()


############################################################
# Compiles the combined binaries
# @param binderCppFileName - the name of the C++ binder file
# @param execName - the executable file name
############################################################
def compileFile(binderCppFileName, execName):
	
	print("Compiling...")
	
	# Run the process
	# TODO: run the g++ compiler in order to compile backbinder.cpp
	# If the compilation succeeds, print "Compilation succeeded"
	# If compilation failed, then print "Compilation failed"	
	# Do not forget to add -std=gnu++11 flag to your compilation line

	retVal = None

	try:
		build = subprocess.check_output(["/usr/bin/g++", "-std=gnu++11", binderCppFileName, "-o", execName], stderr=subprocess.STDOUT)
		return 0
	except subprocess.CalledProcessError as ex:
		retVal = ex.returncode
	except OSError:
		print("ERROR: cannot locate g++")

	return retVal


generateHeaderFile(sys.argv[1:], FILE_NAME)
if compileFile("binderbackend.cpp", "bound") == 0:
	print("Compilation succeeded")
else:
	print("Compilation failed")
