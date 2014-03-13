///////////////////////////////////////////////////////////////////////////////
/////// THE MAIN PROCESSING LOOP
///////////////////////////////////////////////////////////////////////////////	
    ignore=0;
	offset = 0;
	processCommand = 0;
	
	SHA1GeneratePassword(3, password2);
	SHA1GeneratePassword(6, password3);
	SHA1GeneratePassword(0, password4);
	
	mainHostState = HOST_CRYPTO;
	
	
	while (1){ 
		iocb.ioctl_code = VOS_IOCTL_COMMON_GET_RX_QUEUE_STATUS;
		iocb.get.queue_stat = 0;
		vos_dev_ioctl(hUSBSLAVE_FT232, &iocb);
#ifdef TERMINAL_ON
#ifdef PRINT_USB_EXT
        writeString(hUart, "-");
#endif
#endif
        writeString(hUart, "-");
		if (iocb.get.queue_stat == 0)
		{
			vos_delay_msecs(5); // free processor for other threads
			continue;
		} // if the buffer is empty, try again

#ifdef TERMINAL_ON
#ifdef PRINT_USB_EXT
        writeString(hUart, "|");
#endif
#endif
///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////
		i = 0;
		while ((i<offset)&&(uartDataTemp[i]!=0xa)&&(uartDataTemp[i]!=0xd)){
		    i++;
		}
		if (i<offset){ // a valid command is already in the working buffer
			processCommand = 1;
		} else { // read new line
		    if (iocb.get.queue_stat<BUFFER_SIZE-offset){
				validChars = iocb.get.queue_stat;
			} else {
			    validChars = BUFFER_SIZE-offset;
			}
			vos_dev_read(hUSBSLAVE_FT232, &uartDataTemp[offset], (uint16)validChars, &bytesTransferred);
			// get the data to process to userDataTemp buffer
			i=0;
			while((uartDataTemp[i+offset]!=0xa)&&(uartDataTemp[i+offset]!=0xd)&&(i<bytesTransferred)){
                // try to find end of line = end of command
		        i++;
		    }
			if (i>=BUFFER_SIZE){ // error - too long line, we may read just a char
							     // at a time so check the complete length
		    // get rid of the line - 160 chars and set a flag to ignore everything till next \n
				ignore = 1;
				offset = 0;
			} else if (ignore){
			    vos_memcpy(&uartDataTemp, &(uartDataTemp[i]), bytesTransferred+offset-i);
				offset = offset+(unsigned char)bytesTransferred-i; // set the offset to no of valid characters
			} else if ((uartDataTemp[i+offset]==0xa)||(uartDataTemp[i+offset]==0xd)){
				processCommand = 1;
			} else {
			    offset += i;
			}
		}
		//default answer is ERRxxx = 6 characters
		validChars=6;
		strcpy((char*)uartDataOut, ERR_LOWERCASE);
		if (processCommand){
            // switch the blue LED for the duration of command processing
#ifdef PINS_32NEW
            LEDState = LED_LONG_ON|LED_ON_ON;
#else
            LEDState = LED_BUSY_ON|LED_LONG_OFF|LED_ON_ON;
#endif
            vos_gpio_write_port(GPIO_PORT_B, LEDState);
                
			operationCounter += 1;
			// here we can do the processing!
			if (strncmp((char*)uartDataTemp, "GETID",5)==0){
				operation = CMD_STATUS;
				validChars = typeID(uartDataOut);
			} else if (strncmp((char*)uartDataTemp, "GETCOUNTER",10)==0){
				operation = CMD_STATUS;
				validChars = 0;
			} else if (strncmp((char*)uartDataTemp, "GETDELAY",8)==0){
				operation = CMD_STATUS;
				uartDataOut[0]=0x30+scribCmdDelay/10;
				uartDataOut[1]=0x30+(scribCmdDelay%10);
				validChars=2;
			} else if (strncmp((char*)uartDataTemp, "GETINITKEY",10)==0){
				operation = CMD_MANAGEMENT;
				if ((scribStatus&FLASH_INIT_LOCKSEED)==0){
					validChars=(unsigned char)getInitKey(uartDataOut);
				} else { // we are operational -> error
                    strcpy((char*)uartDataOut, ERR_CMD);
                    validChars = strlen(ERR_CMD);
                }
			} else if (strncmp((char*)uartDataTemp, "SETINITKEY",10)==0){
				operation = CMD_MANAGEMENT;
				if ((scribStatus&FLASH_INIT_LOCKSEED)==0){
					vos_memcpy(uartDataOut, &uartDataTemp[11], 8);
                    //setInitKey takes 44 bytes, computes CRC and if correct, sets the initialisation key
					validChars=(unsigned char)setInitKey(&uartDataTemp[11]);
					if (validChars>0){
						SHA1GeneratePasswords();
						SHA1GeneratePassword(3, password2);
						SHA1GeneratePassword(6, password3);
						SHA1GeneratePassword(0, password4);
						validChars = 8; // return the first 8 digits of the received initialisation key
					} else {
						strcpy((char*)uartDataOut, ERR_PARAMS);
						validChars=strlen(ERR_PARAMS);
					}
				}  else { // we are operational -> error
                    strcpy((char*)uartDataOut, ERR_CMD);
                    validChars = strlen(ERR_CMD);
                }
			} else if (strncmp((char*)uartDataTemp, "GETPASSWD",9)==0){
				operation = CMD_MANAGEMENT;
				if ((scribStatus&FLASH_INIT_LOCKSEED)==0){
					validChars=32;
					if (uartDataTemp[10]=='2')
						vos_memcpy(uartDataOut, password2, 32);
					else if (uartDataTemp[10]=='3')
						vos_memcpy(uartDataOut, password3, 32);
					else if (uartDataTemp[10]=='4')
						vos_memcpy(uartDataOut, password4, 32);
					else {
						vos_memcpy(uartDataOut, ERR_PARAMS, 6);
						validChars = 6;
					}
				} else { // we are operational -> error
                    strcpy((char*)uartDataOut, ERR_CMD);
                    validChars = strlen(ERR_CMD);
                }
			} else if (strncmp((char*)uartDataTemp,   "ENGETID",7)==0){
				operation = CMD_EXECUTION | CMD_REMOTE;
				// de-hexify the data
VOS_ENTER_CRITICAL_SECTION
				for (validChars=8; validChars<72; validChars+=2){ // we expect 2 blocks of AES
					if (uartDataTemp[validChars]>0x39) uartDataTemp[validChars]-=7;
					if (uartDataTemp[validChars+1]>0x39) uartDataTemp[validChars+1]-=7;
					uartDataOut[(validChars-8)/2]=((uartDataTemp[validChars]-0x30)<<4)+
												uartDataTemp[validChars+1]-0x30;
				}				
				vos_memset(uartDataTemp, 0, sizeof(uartDataTemp));
VOS_EXIT_CRITICAL_SECTION // we want to be quick now
				DecryptBlocks((unsigned char *)uartDataOut, password4, 2); //decrypt 2 blocks
				// hexify the result so we can use a universal SCRAMBLE function
				validChars=32;
				validChars = uartDataOut[validChars-1];
                // check the format = correct key and data
				if (validChars != 14){ // we expect exactly 14 padding bytes
					vos_memcpy(uartDataOut, ERR_CRYPTO, 6);
					validChars = 6;
				} else {
					for (j = 32-validChars; j<32; j++){
						if (uartDataOut[j]!=validChars)
							break; 
					}
					if (j<32){
						vos_memcpy(uartDataOut, ERR_CRYPTO, 6);
						validChars = 6;
					} else {
						// get dongle ID
						hostCopyROM(&uartDataTemp[9], flashID);
                        // check that this dongle is actually being queried - ID is correct
						for (j = 10; j<18; j++){
							if (uartDataOut[j]!=uartDataTemp[j])
								break; 
						}
						if (j<18){ // incorrect ID
							vos_memcpy(uartDataOut, ERR_PARAMS, 6);
							validChars = 6;
						} else {
							// uartDataOut[8-15]
							// GETCOUNTER
							validChars=18;
							for (j=0; j<4; j++){
								uartDataOut[validChars]=(operationCounter>>(8*(3-j)))&0xff;
								validChars++;
							}
							for (j=validChars; j<32; j++){
								uartDataOut[j]=10; //padding bytes
							}
							// now we need to encrypt it - we do 2 blocks in-situ in uartDataOut
							EncryptBlocks(uartDataOut, password4, 2);
							// and hexify the result
							for (j=32; j > 0; j--) { // 8 bytes
								ch=uartDataOut[j-1];
								if ((ch>>4)<=9)
									uartDataOut[j*2-2]=(ch>>4)+0x30;
								else 
									uartDataOut[j*2-2]=(ch>>4)+0x37;
								if ((ch&0xf)<=9)
									uartDataOut[j*2-1]=(ch&0xf)+0x30;
								else 
									uartDataOut[j*2-1]=(ch&0xf)+0x37;
							}
							validChars = 64;
						}
					}
				}
			} else if (strncmp((char*)uartDataTemp, "ENSCRAMBLE",10)==0){
				operation = CMD_EXECUTION | CMD_REMOTE;
				// de-hexify the data
VOS_ENTER_CRITICAL_SECTION // we want to be quick again
				for (validChars=11; validChars<139; validChars+=2){
					if (uartDataTemp[validChars]>0x39) uartDataTemp[validChars]-=7;
					if (uartDataTemp[validChars+1]>0x39) uartDataTemp[validChars+1]-=7;
					uartDataOut[(validChars-11)/2]=((uartDataTemp[validChars]-0x30)<<4)+
												uartDataTemp[validChars+1]-0x30;
				}				

				vos_memset(uartDataTemp, 0, sizeof(uartDataTemp));
VOS_EXIT_CRITICAL_SECTION
				DecryptBlocks((unsigned char *)uartDataOut, password4, 4); //decrypt 4 blocks
VOS_ENTER_CRITICAL_SECTION
				// set the length and get rid of padding
				validChars=64;
				j = uartDataOut[validChars-1];
				if ((j < 2)||(j>52)){ // padding must be at least 2 bytes
					vos_memcpy(uartDataOut, ERR_CRYPTO, 6);
					validChars = 6;
				} else {
					validChars = j;
					// check all bytes of padding
					for (j = 64-validChars; j<64; j++){
						if (uartDataOut[j]!=validChars)
							break; 
					}
					if (j<64){ // if a byte is not correct -> error
						vos_memcpy(uartDataOut, ERR_CRYPTO, 6);
						validChars = 6;
					} else {
                        // we have to be careful as the content may be completely random
						validChars = 64 - validChars; // Get the length of the message
						vos_memcpy(uartDataTemp, uartDataOut, validChars);  
						////////////////////////////////////////////////////////
						////////////////////////////////////////////////////////
						// 11 - length of counterS + space
						// counterS must be followed by ' '
						for (j=10; j>0; j--){ // verify the length of counterS
							if (uartDataTemp[j]==0x20) // search for a space
								break;
						}
						if (j!=10){
							vos_memcpy(uartDataOut, ERR_PARAMS, 6);
							validChars = 6;
						} else {
                            // we originally accepted shorter counterS - j
VOS_EXIT_CRITICAL_SECTION
							validChars=scramblePassword(validChars, 0, j+1, j+1);
VOS_ENTER_CRITICAL_SECTION
						}
						// we have original challenge (10 bytes, enc. password 32 bytes, and salt
						// add operation counter - 4 bytes
						for (j=0; j<4; j++){
							uartDataOut[validChars]=(operationCounter>>(8*(3-j)))&0xff;
							validChars++;
						}
						for (j=validChars; j<64; j++){
							uartDataOut[j]=(64-validChars);
						}
VOS_EXIT_CRITICAL_SECTION
						// now we need to encrypt it
						EncryptBlocks(uartDataOut, password4, 4);
VOS_ENTER_CRITICAL_SECTION
						// and hexify the result
						for (j=64; j > 0; j--) { // 8 bytes
							ch=uartDataOut[j-1];
							if ((ch>>4)<=9)
								uartDataOut[j*2-2]=(ch>>4)+0x30;
							else 
								uartDataOut[j*2-2]=(ch>>4)+0x37;
							if ((ch&0xf)<=9)
								uartDataOut[j*2-1]=(ch&0xf)+0x30;
							else 
								uartDataOut[j*2-1]=(ch&0xf)+0x37;
						}
						validChars = 128;
					}
				}
VOS_EXIT_CRITICAL_SECTION
			} else if (strncmp((char*)uartDataTemp, "SCRAMBLE",8)==0){
				operation = CMD_EXECUTION;
				validChars = scramblePassword((unsigned short)i, (unsigned short)offset, 9,0);
			} else if (strncmp((char*)uartDataTemp, "SETDELAY",8)==0){
				operation = CMD_EXECUTION;
				scribCmdDelay=(uartDataTemp[9]-0x30)*10+(uartDataTemp[10]-0x30);
                // incorrect delay value will be ignored
				if (scribCmdDelay>99) scribCmdDelay=0;
				flashWrite(FLASH_CMD_DELAY, (unsigned char *)&scribCmdDelay, FLASH_CMD_DELAY_SIZE, FALSE);
				uartDataOut[0]=0x30+scribCmdDelay/10;
				uartDataOut[1]=0x30+(scribCmdDelay%10);
				validChars=2;
			} else if (strncmp((char*)uartDataTemp, "GETCLUSTER",10)==0){
				operation = CMD_STATUS;
				SHA1GeneratePassword(9, uartDataOut);
				vos_memset(uartDataOut+10, 0, 40); //delete unecessary bytes of the computed password - just 10 chars for cluster ID
				validChars = 10;
			} else if (strncmp((char*)uartDataTemp, "GETLOCKED", 9)==0){
				operation = CMD_STATUS;
				if ((scribStatus&FLASH_INIT_LOCKSEED)==0){
					uartDataOut[0] = 0x30;
				} else {
					uartDataOut[0] = 0x31;
				}
				validChars = 1;
			} else {
			    vos_memcpy(uartDataOut, ERR_CMD, 6);
				validChars = 6;
			}
			
			// append the operation counter
			if ((operation & CMD_REMOTE)==0){
				if (validChars>0){
					uartDataOut[validChars]=0x20; validChars+=1;
				}

				for (j=0; j < 4; j++) { // 8 bytes of dongle counter
					ch=(operationCounter>>(8*(3-j)))&0xff;
					if ((ch>>4)<=9)
						uartDataOut[validChars]=(ch>>4)+0x30;
					else 
						uartDataOut[validChars]=(ch>>4)+0x37;
					validChars+=1;
					if ((ch&0xf)<=9)
						uartDataOut[validChars]=(ch&0xf)+0x30;
					else 
						uartDataOut[validChars]=(ch&0xf)+0x37;
					validChars+=1;
				}
			}
			uartDataOut[validChars]=0x0a;
			validChars++;			
			//get rid of the command once processed
			vos_memcpy(&uartDataTemp[0], &uartDataTemp[i+offset], BUFFER_SIZE-offset-i);
        	vos_dev_write(hUSBSLAVE_FT232, uartDataOut, validChars, (uint16*)&offset);
			processCommand=0; offset=0;
			
			if ((operation&CMD_EXECUTION) && ((scribStatus&FLASH_INIT_LOCKSEED) == 0)){
				scribStatus&=(~FLASH_INIT_NO_TIME);
				scribStatus |= (FLASH_INIT_LOCKSEED);  // update the register in EEPROM
				flashWrite(FLASH_INIT, (unsigned char *)&scribStatus, FLASH_INIT_SIZE, FALSE);
			}
			
			// wait if the delay is set
			if (scribCmdDelay>0)
				vos_delay_msecs(scribCmdDelay*10);

            // switch the blue LED Off - we finished processing
#ifdef PINS_32NEW
            LEDState = LED_LONG_OFF|LED_ON_ON;
#else
            LEDState = LED_BUSY_OFF|LED_LONG_OFF|LED_ON_ON;
#endif
            vos_gpio_write_port(GPIO_PORT_B, LEDState);
        }
		// save another time measurement - source of randomness
		if (timingsIndex<SEED_MINIMUM_SAMPLES){ // so that we dont get beyond the array boundary
			// set the tmr_iocb context is it will not be changing
			// we wait for a command from the PC and read the timer - to collect random data
			tmr_iocb.ioctl_code = VOS_IOCTL_TIMER_GET_CURRENT_COUNT;
		    status=vos_dev_ioctl(hTimerRND, &tmr_iocb); /* get current value of timer */
			timings[timingsIndex++] = tmr_iocb.param;
			actualSeed[timingsIndex%FLASH_HASH_SIZE] ^= (unsigned char)(tmr_iocb.param&0xff);
		} else {
		    // update random pool
			updateSeedPool((unsigned char*)&timings, timingsIndex);
			timingsIndex=0;
		}
#ifdef PRINT_TIMER
        writeString(hUart,"Timer: ");
        writeShort(hUart, timerCount);
        writeString(hUart, "\n");
#endif

    }  // while (1) - run forever
