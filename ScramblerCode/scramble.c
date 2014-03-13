// scramblePassword(validChars, 0, j+2, 10);	
///////////////////////////////////////////////////////////////////////////////
// msgLength - the total length of data passed in the function
// offset - if there is anything left at the beginning of the buffer
// ignorePrefix - the initial part of the message to be skipped when search for 
//                salt length
// outputPrefix - space to be left empty at the beginning of the output data
//   outputPrefix must be smaller or equal to ignorePrefix
unsigned short scramblePassword(unsigned short msgLength, unsigned short offset, 
								unsigned short ingorePrefix, unsigned char outputPrefix){
	unsigned short saltLength, commandChars=ingorePrefix, i;
	unsigned short saltStart = ENCRYPTED_PWD_LEN+outputPrefix; //we will return the salt at this offset
	
	// find the first space first - that will be followed by salt length
	// anything before the space is the password
VOS_ENTER_CRITICAL_SECTION
	if (offset>0){
		vos_memcpy(uartDataTemp, uartDataTemp+offset, msgLength);
	}
	
	while ((uartDataTemp[ingorePrefix]!=0x20)&&(ingorePrefix<msgLength))
		ingorePrefix++;
VOS_EXIT_CRITICAL_SECTION
		
	// make sure we have 2 more characters in the string - salt length uses 2 characters
	if ((uartDataTemp[ingorePrefix]==0x20)&&(ingorePrefix+2<msgLength)){
		saltLength=(uartDataTemp[ingorePrefix+1]-0x30)*10+(uartDataTemp[ingorePrefix+2]-0x30);

		if (saltLength>16) { //salt can't be more than 16 characters
			vos_memcpy(uartDataOut, ERR_PARAMS, 6);
			return 6;
		}
		
		// saltStart is where the salt shoud start in the output string
VOS_ENTER_CRITICAL_SECTION
		if (ingorePrefix+4 >= msgLength){ // 3 is for: 1 space and 2 bytes for salt length
			saltLength+=100;
		} else {
		    // we need the salt out of way - let's move it backwards 
			// maximum length of the command is 64+1+2+1+16+prefix = 84+prefix, length is 16
			vos_memcpy(&uartDataTemp[BUFFER_SIZE-16], &uartDataTemp[ingorePrefix+4], 16); // followed by salt
		}
		vos_memcpy(&uartDataTemp[outputPrefix], &uartDataTemp[commandChars], (size_t)ingorePrefix-commandChars); 
		vos_memset(&uartDataTemp[outputPrefix+ingorePrefix-commandChars], 0, 32-ingorePrefix+commandChars); // erase 32 charactres - max length of the password
		//and copy the password itself to the beggining
VOS_EXIT_CRITICAL_SECTION
#ifdef AES_SCRAMBLING
        // scramble with AES256
		SHA1ScrambleAES256(password2, password3, 
				(unsigned char*)&uartDataTemp[saltStart], saltLength, &uartDataTemp[outputPrefix]);
#else
        // scramble with SHA1-HMAC
		SHA1ScrambleSHA1HMAC(password2, 32,  
				(unsigned char*)&uartDataTemp[BUFFER_SIZE-16], saltLength, &uartDataTemp[outputPrefix]);
#endif
VOS_ENTER_CRITICAL_SECTION
		if (saltLength>=100){ // >100 means that we create it
			saltLength-=100;
		}

		if (outputPrefix==0){ //SCRAMBLE
			// move backwards where it belongs in the output buffer
			for (commandChars=0; commandChars<saltLength; commandChars++){
				uartDataOut[ENCRYPTED_PWD_LEN*2+commandChars+1] = uartDataTemp[commandChars+BUFFER_SIZE-16];
			}
			uartDataOut[2*ENCRYPTED_PWD_LEN]=0x20; //space between salt and password
			//hexify the password - it starts at index 0 or outputPrefix
			for(commandChars=saltStart; commandChars>outputPrefix; commandChars--){
				uartDataOut[commandChars*2-1]=(uartDataTemp[commandChars-1]&0x0f)+0x30;
				uartDataOut[commandChars*2-2]=(uartDataTemp[commandChars-1]>>4)+0x30;
				if (uartDataOut[commandChars*2-2]>0x39)
					uartDataOut[commandChars*2-2]+=7;
				if (uartDataOut[commandChars*2-1]>0x39)
					uartDataOut[commandChars*2-1]+=7;
			}
//			uartDataOut[64]=0x20; // maximum length of the salt
			commandChars = 2*ENCRYPTED_PWD_LEN; // 32*2 + outputPrefix - length of scrambled password
			if (saltLength>0) {
				commandChars+=saltLength+1;
			}
		} else { // ENSCRAMBLE move password and salt to the output buffer
			for (commandChars=0; commandChars<ENCRYPTED_PWD_LEN+outputPrefix; commandChars++){
				uartDataOut[commandChars] = uartDataTemp[commandChars];
			}
			if (saltLength>0){
				for (commandChars=0; commandChars<saltLength; commandChars++){
					uartDataOut[ENCRYPTED_PWD_LEN+outputPrefix+commandChars] = uartDataTemp[commandChars+BUFFER_SIZE-16];
				}
				commandChars = ENCRYPTED_PWD_LEN + saltLength + outputPrefix; // 32*2 + outputPrefix - length of scrambled password
			} else {
				commandChars = ENCRYPTED_PWD_LEN + outputPrefix; // 32*2 + outputPrefix - length of scrambled password
			}
		}
VOS_EXIT_CRITICAL_SECTION
		
	} else {
		// what we found is not length of the sault
	    vos_memcpy(uartDataOut, ERR_PARAMS, 6);
	    commandChars = 6;
	}
	return commandChars;
}
