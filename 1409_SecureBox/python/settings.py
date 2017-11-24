# -*- coding: utf-8 -*-

import os, shutil, csv, pickle, time, sys
import logging
if sys.platform=='win32':
    from os_windows import *
else:
    from os_mac import *

## silently ignore all print statements
#class NullWriter(object):
#    def write(self, value): pass
#
#sys.stdout = sys.stderr = NullWriter()

# file/folder definitions (use str rather than unicode otherwise special characters seem not to be handled correctly by os.mkdir, etc.)
SBpath = str(os.path.join(os_AppDataFolder,"SecureBox")) # A2 = 2d device; B = 2d user
keyFolder = os.path.join(SBpath,'userkey')
userPrivateIdentityFile = os.path.join(keyFolder,'private.id')
userPublicIdentityFile = os.path.join(keyFolder,'public.id')
_configFile = os.path.join(SBpath,'config.bin')
_currentStateFile = os.path.join(SBpath,'currentstate.bin')
syncStateFolder = os.path.join(SBpath,'syncstate')
SBFolderBase = '_SecureBox_'
UsersFolderBase = '_users'
FilesFolderBase = '_files'
cloudIdentityFileBase = '_SecureBoxPrivateKey'

## print to log file
##logging.basicConfig(filename=os.path.join(SBpath,__name__+'.log'),level=logging.DEBUG)
#logging.basicConfig(filename='debug.log',level=logging.DEBUG)
#class LogOut(object):
#    def write(self, value): logging.info(value)
#sys.stdout = LogOut()
#class LogErr(object):
#    def write(self, value): logging.error(value)
#sys.stderr = LogErr()
        



# Identity object encapsulates user ID and RSA key
class Identity:
    ID = []
    firstname = []
    lastname = []
    device = []
    isprivate = []
    key = []
    def export(self,fname):
        w = csv.writer(open(fname, "w"))
        w.writerow(['ID',self.ID])
        w.writerow(['firstname',self.firstname])
        w.writerow(['lastname',self.lastname])
        w.writerow(['device',self.device])
        if self.isprivate:
            w.writerow(['privatekey',self.key])
        else:
            w.writerow(['publickey',self.key])

def importIdentity(fname):
    user = Identity()
    for key, val in csv.reader(open(fname)):
        if key == 'publickey':
            user.isprivate = False;
            user.key = val
        elif key == 'privatekey':
            user.isprivate = True;
            user.key = val
        else:
            setattr(user,key,val)
    return user        

# Folder object stores information on a synchronized folder
class Folder:
    # these 2 first fields must always be filled
    ID = []
    originalname = []
    # the next fields are used only by certain functionalities, might be unfilled in some circumstances
    path = []
    amOwner = [] # already deprecated! not handling ownership for the moment as this is too complicated
    key = []

# TaggedKey object contains a folder key encrypted for a specific user
class TaggedKey:
    identity = []
    lockedkey = []
    def save(self,fname):
        pickle.dump(self,open(fname,'w'))

def importTaggedKey(fname):
    return pickle.load(open(fname))

# Config object stores constant variables
class Config:
    dropboxDir = []
    def save(self):
        pickle.dump(self,open(_configFile,'w'))

def config():
    return pickle.load(open(_configFile))


# CurrentState object stores variables that change along the usage of SecureBox
class CurrentState:
    def __init__(self):
        self.folderList = dict()
        self.friends = dict()
    def save(self):
        pickle.dump(self,open(_currentStateFile,'w'))
        
def currentState():
    return pickle.load(open(_currentStateFile))

# Usefull shortcuts
def myself():
    return importIdentity(userPublicIdentityFile)   
def myprivatekey():
    return importIdentity(userPrivateIdentityFile).key
def getSBdir(folderID):
    return os.path.join(config().dropboxDir,SBFolderBase+folderID)
def cloudIdentityFile():
    return os.path.join(config().dropboxDir,cloudIdentityFileBase)

# Init settings
def init(dropboxDir):
    # remove main folder
    if os.path.isdir(SBpath):
        shutil.rmtree(SBpath,True)
        time.sleep(.1) # make sure the folder has been properly deleted before continuing      
    
    # create folders
    if not os.path.isdir(SBpath):
        os.mkdir(SBpath)
        time.sleep(.1) # make sure the folder has been properly created before continuing
    if not os.path.isdir(keyFolder):
        os.mkdir(keyFolder)
    if not os.path.isdir(syncStateFolder):
        os.mkdir(syncStateFolder)
        
    # init config
    cfg = Config()
    cfg.dropboxDir = dropboxDir
    cfg.save()
    
    # init current state
    c = CurrentState()
    c.save()


if __name__ == "__main__":
    f1 = '/Users/thomasdeneux/Dropbox/_SecureBox_test58MSBcmsk8ajT3i/_users/thomasdeneuxgZFrEnmQr4VKu5'
    f2 = '/Users/thomasdeneux/Dropbox/_SecureBox_paperassesrangementseZppZYRmds7Q5F/_users/cypriengodardmKUzBUpmcitHxV'
        
    tk = importTaggedKey(f1)
    tk = importTaggedKey(f2)
    