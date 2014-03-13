
// saltLength - if a new salt is required than the value is 100+the required length	
// key - password 2
// saltLength - if >100 -> salt has to be created
void SHA1ScrambleSHA1HMAC(unsigned char *key, unsigned char keyLength, 
	unsigned char *salt, unsigned short saltLength, unsigned char *data){
	aes256_context aesContext;
	unsigned char tdata[16];
	unsigned char newSalt[48];
	unsigned char i,j;

	if (saltLength >100){
		if (saltLength>116) saltLength=16; else saltLength-=100;
        //create the salt using a randomness pool and volatile counter and SHA1
VOS_ENTER_CRITICAL_SECTION
		SHA1Init(&sha_ctx);
		SHA1Update(&sha_ctx, actualSeed, FLASH_SEED_NOW_SIZE);
		OTPGenerationCounter++;
		SHA1Update(&sha_ctx, (unsigned char*)&OTPGenerationCounter, 2); // add one more byte - as counter
		SHA1Result(&sha_ctx, newSalt);

		// convert values to ASCII
		for (i = 0; i<saltLength; i++){
			j = newSalt[i]&0x3f;
			if (j<10){
				salt[i]=j+48; // digits
			} else if (j<(10+26)){
				salt[i]=j+65-10; // uppercase letters
			} else if (j<(10+26+26)){
				salt[i]=j+97-10-26; // lowercase letters
			} else {
				salt[i]=j+10; // values 62 and 63 are mapped to H and I
			}
		}
	} else if (saltLength>16){
		saltLength=16;
	}

	vos_memset(newSalt, 0, sizeof(newSalt));
	vos_memcpy(newSalt, data, 32);
	vos_memcpy(newSalt+32, salt, saltLength);
    // and do the SHA1-HMAC
	SHA1HMAC(key, keyLength, newSalt, 48, data);
VOS_EXIT_CRITICAL_SECTION
	// the first 20 bytes of data contains the HMAC value
}	


////////////////////////////////////////////////////////////////////////////////
/** HMAC-SHA1 computation function
    key / password - must not be longer than 64 bytes
    @return void.
*/
void SHA1HMAC(unsigned char *key, unsigned int keyLength, unsigned char *in,
             unsigned int inLength, unsigned char *result) {
    unsigned char tempBuf[20];
    unsigned char block[64];
	int i;

    /* Compute INNERHASH from KEY and IN.  */
    vos_memset(block, 0x36, sizeof(block));
    for (i=0; i<keyLength; i++) {
	    block[i]=block[i]^key[i];
    }

    SHA1Init(&sha_ctx);
    SHA1Update(&sha_ctx, block, sizeof(block));
	SHA1Update(&sha_ctx, in, (unsigned short)inLength);
    SHA1Result(&sha_ctx, tempBuf);
    /* Compute result from KEY and INNERHASH.  */

    vos_memset (block, 0x5c, sizeof (block));
	for (i=0; i<keyLength; i++) {
	    block[i]=block[i]^key[i];
    }

    SHA1Init(&sha_ctx);

    SHA1Update(&sha_ctx, block, 64);
    SHA1Update(&sha_ctx, tempBuf, 20);

    SHA1Result(&sha_ctx, result);
}

