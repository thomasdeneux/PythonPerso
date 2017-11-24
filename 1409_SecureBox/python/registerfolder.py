# -*- coding: utf-8 -*-
"""
Created on Wed Sep 10 10:55:39 2014

@author: THomas
"""

import sys, os, shutil, glob, time, webbrowser, re

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import settings, crypto
from guibasic import SBDialog
    
############################ SUBFU#############################################
    
    
def getFolder(d):
    # get entire information for folder path d
    c = settings.currentState();
    found = False
    for f in c.folderList.itervalues():
        if d==f.path:
            found = True
            break
    if found:
        return f
    else:
        return None
    
def listUnsyncFolders(): # returns incomplete Folder object with filled fields ID and originalname only
    folderList = settings.currentState().folderList;
    syncIDs = folderList.keys()
    
    basename = os.path.join(settings.config().dropboxDir,settings.SBFolderBase)
    nbase = len(basename)
    names = glob.glob(basename+"*")
    allIDs = [x[nbase:] for x in names]

    myID = settings.myself().ID
    
    unsyncIDs = list(set(allIDs)-set(syncIDs))
    unsync,invited,waiting,corrupted = [],[],[],[]
    for folderID in unsyncIDs:
        ddir = basename+folderID
        udir = os.path.join(ddir,settings.UsersFolderBase)
        f = settings.Folder()
        f.ID = folderID
        if not os.path.isdir(os.path.join(ddir,'_files')) or not os.path.isdir(udir) or not os.path.isfile(os.path.join(ddir,'_folderoriginalname')):
            corrupted.append(f)
        else:
            f.originalname = open(os.path.join(basename+folderID,'_folderoriginalname')).read()
            if os.path.exists(os.path.join(udir,myID)):
                unsync.append(f)
            elif os.path.exists(os.path.join(udir,"W_"+myID)):
                waiting.append(f)
            else:
                invited.append(f)
    
    return unsync,invited,waiting,corrupted

def isSubDir(path, directory):
    path = os.path.realpath(path)
    directory = os.path.realpath(directory)
    relative = os.path.relpath(path, directory)
    if relative.startswith(os.pardir + os.sep):
        return False
    else:
        return True
    
def isValidLocalFolder(d,err1="is already being synchronized",err2="is not a valid local folder",err3=""):
    c = settings.currentState()
    msg = ''
    for val in c.folderList.itervalues():
        if d == val.path:
            msg = "Folder '"+d+"' "+err1+"."
        elif isSubDir(d,val.path):
            msg = "Folder '"+d+"' "+err2+", as its parent folder '"+val.path+"' is already being synchronized."+err3
        elif isSubDir(val.path,d):
            msg = "Folder '"+d+"' "+err2+", as its child folder '"+val.path+"' is already being synchronized."
        if msg != '':
            QMessageBox.warning(None,"Secure Box",msg)
            return False
    DB = settings.config().dropboxDir
    msg = ''
    if d == DB or isSubDir(d,DB) or isSubDir(DB,d):
        msg = "A Dropbox folder or a Dropbox parent folder"+err2+"."
        QMessageBox.warning(None,"Secure Box",msg)
        return False    
    return True
    


############################ ACTIONS ##########################################


def registerFolder(d=None):
    if d is None:
        d = QFileDialog.getExistingDirectory(None,"Select folder to synchronize")
        if d=="":
            return
            
    print('adding '+d)
    
    # check that folder does not intersect any folder that is already being synchronized
    if not isValidLocalFolder(d,err2="cannot be synchronized",err3=" Please first unregister the child folder."):
        return
       
    # add entry to folders list
    f = settings.Folder()
    f.originalname = os.path.basename(d)
    f.ID = re.sub('[^A-Za-z0-9]+', '', f.originalname).lower()+crypto.genID()
    f.path = d
    f.key = crypto.genFolderKey()
    c = settings.currentState();
    c.folderList[f.ID] = f
    
    # create current tree folder   
    wdir = os.path.join(settings.syncStateFolder,f.ID)
    if not os.path.isdir(wdir): # it can happen that the folder failed to be removed at previous unsync
        os.mkdir(wdir)
    
    # create dropbox folders
    ddir = settings.getSBdir(f.ID)
    if not os.path.isdir(ddir): # it can happen that the folder failed to be removed at previous unsync
        os.mkdir(ddir)
    if not os.path.isdir(os.path.join(ddir,settings.UsersFolderBase)): # it can happen that the folder failed to be removed at previous unsync
        os.mkdir(os.path.join(ddir,settings.UsersFolderBase))
    if not os.path.isdir(os.path.join(ddir,settings.FilesFolderBase)): # it can happen that the folder failed to be removed at previous unsync
        os.mkdir(os.path.join(ddir,settings.FilesFolderBase))

    # put original folder name into Dropbox foldr
    open(os.path.join(ddir,"_folderoriginalname"),'w').write(f.originalname)

    # put encrypted key into Dropbox folder
    tk = settings.TaggedKey()
    tk.identity = settings.myself()
    tk.lockedkey = crypto.encryptKey(f.key,tk.identity.key)
    tk.save(os.path.join(ddir,settings.UsersFolderBase,tk.identity.ID)) 
    
    # save the new entry in folder list only if everything went ok
    c.save()
    
def unregisterFolder(f,flag="removecloud"): # flag can be "stopsync" or "removecloud" 
    # look for folder in folder list if argument was a path
    if f.__class__.__name__ == 'str':
        f = getFolder(f)
        if f is None:
            QMessageBox.warning(None,"Secure Box","Folder '"+d+"' cannot be unregistered, because it is not being currently synchronized.")
            return        

    print('unregistering '+f.ID)
    
    # remove item from folder list 
    c = settings.currentState();
    if f.ID in c.folderList: # can not be the case, when folder is only on the cloud
        c.folderList.pop(f.ID)
        c.save()
    
        # remove current tree folder
        wdir = os.path.join(settings.syncStateFolder,f.ID)
        shutil.rmtree(wdir,True)
    
    # remove dropbox folder
    if flag=="removecloud":
        ddir = settings.getSBdir(f.ID)
        try:
            shutil.rmtree(ddir)
        except:
            QMessageBox.warning(None,"Secure Box","Secure Box encountered an error while trying to remove folder '"+ddir+"'. Please remove it by hand to prevent future errors in Secure Box routines.")            
        time.sleep(.1) # give time to the deletion to occur before possible next attempts to scan the Drobbox folders

def moveFolder(f,dst="",flag="move"): # flag can be "move" or "relocate"
    # look for folder in folder list if argument was a path
    if f.__class__.__name__ == 'str':
        f = getFolder(f)
        if f is None:
            QMessageBox.warning(None,"Secure Box","Folder '"+d+"' cannot be moved, because it is not being currently synchronized.")
            return        
    
    # new folder location
    basename = os.path.basename(f.path)
    if dst=="":
        if flag=='move':
            msg = "Select new location where to move folder '"+basename+"'"
        elif flag=='relocate':
            msg = "Select new location of previous folder '"+basename+"'"
        dst = QFileDialog.getExistingDirectory(None,msg,f.path)
        if dst=="":
            return
        if flag=='move':
            dst = os.path.join(dst,basename)
            
    # check that destination folder is valid
    if flag=='move':
        if os.path.isdir(dst):
            msg = "Cannot move folder '"+basename+"': there is already a folder '"+dst+"'" 
            QMessageBox.warning(None,"Secure Box",msg)
            return
        if not isValidLocalFolder(dst,err2="is not a valid re-location for current folder '"+basename+"'"):
            return
    elif flag=='relocate':
        if dst==f.path or isSubDir(dst,f.path):
            QMessageBox.warning(None,"Secure Box","Error: '"+f.path+"' was initially detected not to be an existing folder.")
            return
        if isSubDir(f.path,dst):
            # it is valid to relocate the folder to a parent of its previous location
            pass
        elif not isValidLocalFolder(dst,err2="is not a valid new location for previous folder '"+basename+"'"):
            return

    # move content if it is a "move"
    if flag=="move":            
        shutil.move(f.path,dst) # note that dst does not exist yet, otherwise src would be moved to inside dst!
        try:
            os.rmdir(f.path)
        except:
            print(sys.exc_info())
   
    # update item in folder list
    c = settings.currentState();
    c.folderList[f.ID].path = dst
    c.save()
    
def syncFolder(f,d=None,flag='fromzero'): # flag: 'fromzero' or 'reconnect'
    '''Synchronize cloud folder with local directory
    
    note that f.ID and f.orginalpath should already be set
    '''
    if d is None:
        if flag=="fromzero":
            d = QFileDialog.getExistingDirectory(None,"Select parent location for folder '"+f.originalname+"'")
            if d=="":
                return
            d = os.path.join(d,f.originalname)
        elif flag=="reconnect":
            d = QFileDialog.getExistingDirectory(None,"Select current location of local folder '"+f.originalname+"'")
           
    c = settings.currentState();
    print('adding '+d)
    
    # check that folder does not intersect any folder that is already being synchronized
    if not isValidLocalFolder(d):
        return
    
    # create the folder if needed
    if not os.path.isdir(d):
        os.mkdir(d)
        
    # decrypt the folder key currently inside the Dropbox folder
    ddir = settings.getSBdir(f.ID)
    myID = settings.myself().ID
    tk = settings.importTaggedKey(os.path.join(ddir,settings.UsersFolderBase,myID)) 
    f.key = crypto.decryptKey(tk.lockedkey,settings.myprivatekey())

    # add entry to folders list
    f.path = d
    c.folderList[f.ID] = f
    
    # create current tree folder   
    wdir = os.path.join(settings.syncStateFolder,f.ID)
    if not os.path.isdir(wdir): # it can happen that the folder failed to be removed at previous unsync
        os.mkdir(wdir)
    
    # save the new entry in folder list only if everything went ok
    c.save()

class SelectFriendDialog(SBDialog):
    def __init__(self,d):
        SBDialog.__init__(self)

        self.selectedFriendNames = [];
        self.selectedFriendID = [];

        layout = QVBoxLayout();

        label = QLabel();
        txt = "<h3>You are about to share folder '"+d+"'.</h3>" \
            + "<p>Select in your contact list below with whom you want to share it.</p>"
        label.setText(txt)
        label.setWordWrap(True)
        layout.addWidget(label)

        self.combo = QComboBox()
        c = settings.currentState()
        for (key,val) in c.friends.iteritems():
            self.combo.addItem(val.firstname+" "+val.lastname,val.ID)
        self.combo.activated.connect(self.getFriend)
        layout.addWidget(self.combo)
        
        self.namesList = QLabel();
        self.namesList.setWordWrap(True)
        layout.addWidget(self.namesList)

        label = QLabel();
        txt = "<p>You will now be directed to a Dropbox web page, where you should share the encrypted Dropbox folder with these persons." \
            + " You can also share it with people who are not in your contact list, then they will be added to it."
        label.setText(txt)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        ok = QPushButton()
        ok.setText('OK')
        ok.clicked.connect(self.close)
        layout.addWidget(ok)

        self.setLayout(layout)

    def getFriend(self):
        self.selectedFriendNames.append(self.combo.itemText(self.combo.currentIndex()))
        self.selectedFriendID.append(self.combo.itemData(self.combo.currentIndex()).toString())
        txt = reduce(lambda x,y:x+","+y,self.selectedFriendNames)
        txt = "<font color=#777777>"+txt+"</font>"
        self.namesList.setText(txt)
        
    @staticmethod
    def selectFriend(d):
        D = SelectFriendDialog(d)
        D.exec_()
        return D.selectedFriendID


def shareFolder(f): 
    # dialog explains to user what will happen, and let him select contacts from friends list
    basename = os.path.basename(f.path) if not f.path==[] else f.originalname
    friendIDs = SelectFriendDialog.selectFriend(basename)

    # already encrypt folder key for selected friends
    for friendID in friendIDs:
        shareKey(f.ID,friendID,True)
        
    # direct user to Dropbox page for sharing encrypted folder
    webbrowser.open("https://www.dropbox.com/home/"+settings.SBFolderBase+f.ID+"?share=1")


def joinFolder(folderID):
    print('joining folder '+folderID)
    user = settings.myself()
    fname = os.path.join(settings.getSBdir(folderID),settings.UsersFolderBase,"W_"+user.ID) 
    user.export(fname)

def joinInvitedFolders():
    unsync,invited,waiting,corrupted = listUnsyncFolders()
    for f in invited:
        joinFolder(f.ID)
    
def shareKey(folderID,friendID,isContact=False):
    print('sharing key for folder '+folderID+' to '+friendID)
    udir = os.path.join(settings.getSBdir(folderID),settings.UsersFolderBase) 
    c = settings.currentState()
    
    # get friend identity        
    wname = os.path.join(udir,"W_"+friendID)
    if isContact:
        friend = c.friends[friendID]
    else:
        friend = settings.importIdentity(wname)
        c.friends[friend.ID] = friend; 
        c.save()
        
    # share (encrypted) key with him
    tk = settings.TaggedKey()
    tk.identity = friend
    if folderID in c.folderList:
        folderkey = c.folderList[folderID].key
    else:
        myID = settings.myself().ID
        encryptedkey = settings.importTaggedKey(os.path.join(udir,myID)).lockedkey
        folderkey = crypto.decryptKey(encryptedkey,settings.myprivatekey())
    tk.lockedkey = crypto.encryptKey(folderkey,friend.key)
    tk.save(os.path.join(udir,friend.ID))
    if os.path.isfile(wname):
        os.remove(wname)

def shareRequestedKeys():
    DB = settings.config().dropboxDir
    basename = os.path.join(DB,settings.SBFolderBase)
    nbase = len(basename)
    names = glob.glob(basename+"*")
    folderIDs = [x[nbase:] for x in names]

    myID = settings.myself().ID
    
    for folderID in folderIDs:
        udir = os.path.join(DB,settings.SBFolderBase+folderID,settings.UsersFolderBase)
        base = os.path.join(udir,"W_")
        nbase = len(base)
        wnames = glob.glob(base+"*")
        friendIDs = [x[nbase:] for x in wnames]
        for friendID in friendIDs:
            if os.path.isfile(os.path.join(udir,myID)):            
                shareKey(folderID,friendID)        
    
def detectNewContacts():
    DB = settings.config().dropboxDir
    basename = os.path.join(DB,settings.SBFolderBase)
    nbase = len(basename)
    names = glob.glob(basename+"*")
    folderIDs = [x[nbase:] for x in names]

    myID = settings.myself().ID
    c = settings.currentState() 
#    print folderIDs
    for folderID in folderIDs:
        udir = os.path.join(DB,settings.SBFolderBase+folderID,settings.UsersFolderBase)
        base = os.path.join(udir,"*")
        nbase = len(udir)+1
        names = glob.glob(base+"*")
        for name in names:
#            print name
            friendID = name[nbase:]
            if friendID[:2]=="W_" or friendID==myID or friendID in c.friends: # 
                continue
            try:
                tk = settings.importTaggedKey(name)
                c.friends[friendID] = tk
                c.save()
            except:
                print("file '"+name+"' is not a valid taggedkey file")
    
############################ PRIVATE KEY MANAGEMENT ###########################

def idRemoveFromCloud():
    os.remove(settings.cloudIdentityFile())

def idPutOnCloud():            
    (password,ok) = QInputDialog.getText(None,"Secure Box","Enter password to protect your identity file on cloud")
    password = str(password) # convert from unicode string to byte array
    crypto.encryptFile(open(settings.userPrivateIdentityFile,'rb'),open(settings.cloudIdentityFile(),'wb'),password)
            
############################ MAIN #############################################
            

if __name__ == "__main__":

#    app = QApplication(sys.argv)

#    print(SelectFriendDialog.selectFriend('blabla'))
    
#    d = QFileDialog.getExistingDirectory(None,"Select folder to synchronize")
#    registerFolder(d)

#    joinInvitedFolders()
#    shareRequestedKeys()

#    detectNewContacts()

    f1 = '/Users/thomasdeneux/Dropbox/_SecureBox_test58MSBcmsk8ajT3i/_users/thomasdeneuxgZFrEnmQr4VKu5'
    f2 = '/Users/thomasdeneux/Dropbox/_SecureBox_paperassesrangementseZppZYRmds7Q5F/_users/cypriengodardmKUzBUpmcitHxV'
        
    tk = settings.importTaggedKey(f1)
    tk = settings.importTaggedKey(f2)