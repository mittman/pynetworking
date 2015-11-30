/*************************
*** Kevin Mittman ********
**************************/
#include <string>
#include "codearray.h"
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include <vector>
#include <sys/stat.h>
#include <sys/types.h>

//#include <iostream>

using namespace std;

int main()
{
	
	/* The child process id */
	pid_t childProcId = -1;

	/* Go through the binaries */
	for(int progCount = 0; 	progCount < NUM_BINARIES; ++progCount)
	{
			
		//TODO: Create a temporary file you can use the tmpnam() function for this.
		// E.g. fileName = tmpnam(NULL)
		char* fileName = tmpnam(NULL);
			
		
		//TODO: Open the file and write the bytes of the first program to the file.
		//These bytes are found in codeArray[progCount]

		/* Open the file for writing binary values */
		FILE* fp = fopen(fileName, "wb");
	
		/* Make sure the file was opened */
		if(!fp)
		{
			perror("fopen");
			exit(-1);
		}
	
		/* The arguments are as follows:
	 	 * @arg1 - the array containing the elements we would like to write to the file.
	 	 * @arg2 - the size of a single element.
	 	 * @arg3 - the number of elements to write to the file
	 	 * @arg4 - the file to which to write the bytes
	 	 * The function returns the number of bytes written to the file or -1 on error
	 	 */
		if(fwrite(codeArray[progCount], sizeof(char), programLengths[progCount], fp) < 0)
		{
			perror("fwrite");
			exit(-1);
		}
	
		/* Close the file */
		fclose(fp);

		
		//TODO: Make the file executable: this can be done using chmod(fileName, 0777)
		chmod(fileName, 0777);
		

		//TODO: Create a child process using fork
		childProcId = fork();
		//cout << childProcId << endl; /* debugging */

		if (childProcId < 0) { 
			/* error occurred */
			fprintf(stderr, "Fork Failed");
			exit(-1);
		}
		/* I am a child process; I will turn into an executable */
		else if (childProcId == 0) {

			//TODO: use execlp() in order to turn the child process into the process
			//running the program in the above file.
			if(execlp(fileName, fileName, NULL) < 0)
			{
				perror("execlp");
				exit(-1);
			}
		}
		/* parent process */
		else {
		/* parent will wait for the child to complete */
			if(wait (NULL) < 0)
			{
				perror("execlp");	
				exit(-1);
			}
			printf ("Child Complete");
		}

	}
	
	/* Wait for all programs to finish */
	for(int progCount = 0; progCount < NUM_BINARIES; ++progCount)
	{
		/* Wait for one of the programs to finish */
		if(wait(NULL) < 0)
		{
			perror("wait");
			exit(-1);
		}	
	}

	return 0;
}
