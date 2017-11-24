# -*- coding: utf-8 -*-

# Conventions:
# RSA keys are passed as byte strings in PEM format
# AES keys are passed as raw byte strings

import StringIO
from hashlib import md5

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP    
from Crypto.Cipher import AES

import alphabet

####################### GENERATE IDENTITY #####################################

def genID(nbyte=10): # 2^80 ~ 10^24 possibilities, no chance that 2 people in the world get the same ID
    id256 = Random.new().read(nbyte)
    id62 = alphabet.base62_encode(alphabet.string2num(id256))
    return id62
    
def genIdentity():
    ID = genID()
    key = RSA.generate(2048)
    privatekey = key.exportKey('PEM')
    publickey = key.publickey().exportKey('PEM')
    return ID,privatekey,publickey

def derivePublic(privatekey):
    key = RSA.importKey(privatekey)
    publickey = key.publickey().exportKey('PEM')
    return publickey


    
####################### GENERATE FOLDER KEY ###################################
 
def genFolderKey():
    return Random.new().read(32)


####################### FILE ENCRYPTION/DECRYPTION ############################

def derive_key_and_iv(folderkey, salt, key_length, iv_length):
    d = d_i = ''
    while len(d) < key_length + iv_length:
        d_i = md5(d_i + folderkey + salt).digest()
        d += d_i
    return d[:key_length], d[key_length:key_length+iv_length]

def encryptFile(in_file, out_file, folderkey, key_length=32):
    bs = AES.block_size
    salt = Random.new().read(bs - len('Salted__'))
    key, iv = derive_key_and_iv(folderkey, salt, key_length, bs)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    out_file.write('Salted__' + salt)
    finished = False
    while not finished:
        chunk = in_file.read(1024 * bs)
        if len(chunk) == 0 or len(chunk) % bs != 0:
            padding_length = bs - (len(chunk) % bs)
            chunk += padding_length * chr(padding_length)
            finished = True
        out_file.write(cipher.encrypt(chunk))
    out_file.close()

def decryptFile(in_file, out_file, folderkey, key_length=32):
    bs = AES.block_size
    salt = in_file.read(bs)[len('Salted__'):]
    key, iv = derive_key_and_iv(folderkey, salt, key_length, bs)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    next_chunk = ''
    finished = False
    while not finished:
        chunk, next_chunk = next_chunk, cipher.decrypt(in_file.read(1024 * bs))
        if len(next_chunk) == 0:
            padding_length = ord(chunk[-1])
            if padding_length < 1 or padding_length > bs:
               raise ValueError("bad decrypt pad (%d)" % padding_length)
            # all the pad-bytes must be the same
            if chunk[-padding_length:] != (padding_length * chr(padding_length)):
               # this is similar to the bad decrypt:evp_enc.c from openssl program
               raise ValueError("bad decrypt")
            chunk = chunk[:-padding_length]
            finished = True
        out_file.write(chunk)
    out_file.close()
        

####################### KEY ENCRYPTION/DECRYPTION #############################



def encryptKey(folderkey, rsakey):
    cipher = PKCS1_OAEP.new(RSA.importKey(rsakey))
    # note that the length of folderkey (32) satisfies being less than 
    # rsakey.size()/8-2-2*cipher._hashObj.digest_size (213)
    return cipher.encrypt(folderkey)

def decryptKey(encryptedfolderkey, rsakey):
    # encryptedfolderkey must be of length 256
    cipher = PKCS1_OAEP.new(RSA.importKey(rsakey))
    return cipher.decrypt(encryptedfolderkey)


        


if __name__ == "__main__":
    print 'generating RSA key'
    ID,privatekey,publickey = genIdentity()

    folderkey = genFolderKey()
    print 'folder key: '+folderkey
    encryptedkey = encryptKey(folderkey, publickey)
    print 'encrypted key: '+encryptedkey
    decryptedkey = decryptKey(encryptedkey, privatekey)
    print 'decrypted key: '+decryptedkey
    
