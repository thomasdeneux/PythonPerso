# -*- coding: utf-8 -*-

import sys, os, time

import sip
sip.setapi('QString',2)

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import settings, registerfolder
from guibasic import SBDialog

class Board(SBDialog):
    def __init__(self):
        SBDialog.__init__(self)
        self.setWindowTitle("Secure Box Board")
        
        # use a subcontainer to easily reset the display
        self.maincontainer = QStackedLayout()
        self.setLayout(self.maincontainer)
        
        # build the board
        self.currentboard = None
        self.buildboard()   
        
        # set a timer to refresh every second
        self.refreshtimer = QTimer()
        self.refreshtimer.setInterval(1000)
        self.refreshtimer.timeout.connect(self.buildboard)
        self.refreshtimer.start(1000)
        
        
    def buildboard(self):
        
        self.layout = QVBoxLayout()
        
        # Identity line
        self.identityLine()
                   
        self.layout.addStretch()
        
        # loop through synchronized folders
        self.maingrid = QGridLayout()
        self.layout.addItem(self.maingrid)
        self.maingrid.setColumnStretch(1,1) # stretch between folder names and actions
        self.nrow = 0
        folderList = settings.FilesFolderBase
        c = settings.currentState()
        folderList = c.folderList
        folderList = settings.currentState().folderList
        for f in folderList.itervalues():
            self.addLine(f,'sync')
            
        # then loop through unsynchronized folders
        unsync,invited,waiting,corrupted = registerfolder.listUnsyncFolders()
        for f in unsync:
            self.addLine(f,'unsync')
        # do not loop through invited folders, as they are only in a transient state - the deamon should soon transform them into 'waiting' folders
        for f in waiting:
            self.addLine(f,'waiting')
        for f in corrupted:
            self.addLine(f,'unsynccorrupted')

        self.layout.addStretch()

        # 'sync new folder' option
        self.nrow = self.nrow+1
        button = QPushButton()
        button.setText("NEW FOLDER")
        button.clicked.connect(lambda:self.action([],"new"))
        line = QHBoxLayout();
        self.layout.addItem(line)
        line.addWidget(button)
        line.addStretch()           

        # update display (was hard to prevent flickering on Mac! -> worked out by using QStackedLayout for maingrid)
        firsttime = (self.currentboard is None)
        if not firsttime:
            prevboard = self.currentboard
        self.currentboard = QWidget()
        self.currentboard.setAttribute(Qt.WA_DeleteOnClose)
        self.currentboard.setLayout(self.layout)
        self.maincontainer.insertWidget(0,self.currentboard)
        if not firsttime:
            self.maincontainer.setCurrentIndex(0) # this line is needed to prevent flicker, but does not seem to change the display as it should!! strange...
            prevboard.close() # currentboard is also deleted because of attribute Qt.WA_DeleteOnClose
        
    def identityLine(self):       
        id = settings.myself();
        f = settings.keyFolder;
        txt = id.firstname + " " + id.lastname
        txt = txt + ' <small>[identity file in ' \
            + '<a href="file:///'+f+'" style="text-decoration: none; color: black">'+f+'</a>'
        fcloud = settings.cloudIdentityFile()        
        if os.path.isfile(fcloud):
            txt = txt + '<a href="file:///'+settings.config().dropboxDir+'" style="text-decoration: none; color: red">'+' and on cloud'+'</a>'
        txt = txt + ']</small>'

        # Layout
        frame = QWidget();
        frame.setStyleSheet("background-color:#ddddee;")
        line = QHBoxLayout();
        frame.setLayout(line)
        self.layout.addWidget(frame)
        label = QLabel()
        label.setText(txt)
        label.setOpenExternalLinks(True)
        line.addWidget(label)
 
        line.addStretch()
               
        button = QPushButton()
        if os.path.isfile(fcloud):
            button.setText("Remove from cloud")
            button.clicked.connect(lambda:self.action(f,"idRmCloud"))
        else:
            button.setText("Put on cloud")
            button.clicked.connect(lambda:self.action(f,"idPutCloud"))
        line.addWidget(button)
        
        
    def addLine(self,f,regstatus):
        self.nrow = self.nrow+1

        # check state
        dbdir = settings.config().dropboxDir
        ddir = os.path.join(dbdir,settings.SBFolderBase+f.ID)
        if regstatus == 'sync':
            if not os.path.isdir(ddir):
                state = 'noDB'
            elif not os.path.isdir(os.path.join(ddir,'_files')) or not os.path.isdir(os.path.join(ddir,'_users')) or not os.path.isfile(os.path.join(ddir,'_folderoriginalname')):      
                state = 'corruptedDB'
            elif not os.path.isdir(f.path):
                state = 'nofolder'
            else:
                state = 'ok'
        else:
            state = regstatus # can be 'unsync' or 'waiting'
            
        # folder name
        label = QLabel()
        if regstatus == 'sync':
            d,base = os.path.split(f.path)
        elif regstatus == 'unsynccorrupted':
            base = f.ID
        else:
            base = f.originalname
        #txt = '<h2><font color="#4444ff">'+base+'</font></h2>';
        txt = '<h2><font color="#cc4444">'+base+'</font></h2>';
        if state=='ok':
            subtxt = f.path;
        elif state=='nofolder':
            subtxt = 'LOCAL FOLDER '+f.path+' DOES NOT EXIST'
        elif state=='noDB':
            subtxt = 'FOLDER INSIDE DROPBOX MISSING!'
        elif state=='corruptedDB':
            subtxt = 'FOLDER INSIDE DROPBOX CORRUPTED!'
        elif state=='unsynccorrupted':
            subtxt = 'CORRUPTED FOLDER FOUND INSIDE DROPBOX!'
        elif state=='unsync':
            subtxt = 'currently not synced on this device'
        elif state=='waiting':
            subtxt = 'waiting for key to shared folder'
        txt = txt+'<small>'+subtxt+'</small>'
        # add a link to open the folder in Explorer
        link = ''
        if state == 'ok':
            link = f.path
        elif state in ['unsync', 'wating', 'corruptedDB', 'unsynccorrupted']:
            link = settings.getSBdir(f.ID)     
        elif state in ['noDB']:
            link = settings.config().dropboxDir
        if link != '':
            txt = '<a href="file:///'+link+'" style="text-decoration: none; color: black">'+txt+'</a>'
        label.setText(txt)
        label.setOpenExternalLinks(True)
        self.maingrid.addWidget(label,self.nrow,1)
        
        # actions    
        if state in ['ok', 'nofolder', 'unsync']:
            button = QPushButton()
            button.setText("Share folder")
            button.clicked.connect(lambda:self.action(f,"share"))
            self.maingrid.addWidget(button,self.nrow,2)
        if state in ['ok', 'nofolder', 'unsync']:
            button = QPushButton()
            if state=='ok':
                button.setText("Move local folder")
                button.clicked.connect(lambda:self.action(f,"move"))
            elif state=='nofolder':
                button.setText("Re-locate folder")
                button.clicked.connect(lambda:self.action(f,"relocate"))
            elif state=='unsync':
                button.setText("Re-connect folder")
                button.clicked.connect(lambda:self.action(f,"reconnect"))
            self.maingrid.addWidget(button,self.nrow,3)
        if state in ['ok', 'nofolder', 'unsync', 'noDB', 'corruptedDB']:
            button = QPushButton()
            if state in ['ok', 'nofolder', 'noDB', 'corruptedDB']:
                button.setText("Stop syncing folder")
                button.clicked.connect(lambda:self.action(f,"stopsync"))
            elif state=='unsync':
                button.setText("Synchronize folder")
                button.clicked.connect(lambda:self.action(f,"startsync"))
            self.maingrid.addWidget(button,self.nrow,4)
        if state in ['ok', 'nofolder', 'unsync', 'unsynccorrupted', 'corruptedDB']:
            button = QPushButton()
            button.setText("Remove from cloud")
            button.clicked.connect(lambda:self.action(f,"removecloud"))
            self.maingrid.addWidget(button,self.nrow,5)
        
    def action(self,f,flag):
        print(flag)
        if flag=="stopsync":
            registerfolder.unregisterFolder(f,flag="stopsync")
        elif flag=="removecloud":
            registerfolder.unregisterFolder(f,flag="removecloud")
        elif flag=="new":
            registerfolder.registerFolder()
        elif flag=="startsync":
            registerfolder.syncFolder(f,flag="fromzero")
        elif flag=="move":
            registerfolder.moveFolder(f,flag="move")
        elif flag=="relocate":
            registerfolder.moveFolder(f,flag="relocate")
        elif flag=="reconnect":
            registerfolder.syncFolder(f,flag="reconnect")
        elif flag=="share":
            registerfolder.shareFolder(f)
        elif flag=="idPutCloud":
            registerfolder.idPutOnCloud()
        elif flag=="idRmCloud":
            registerfolder.idRemoveFromCloud()
        elif flag=="refresh":
            pass # all what we are interested in is the buildboard() instruction below
        self.buildboard()
        
    
        

def launchBoard(arg=[]):
    app = QApplication(arg)
    b = Board()
    b.show()
    app.exec_()


def check(x):
    print(x.text())
  
def test(arg):  
    app = QApplication(arg)
    a = QDialog(None)
    layouta = QVBoxLayout()
    
    b = QWidget(None)    
    buttonb = QPushButton()
    buttonb.setText('click me')
    buttonb.clicked.connect(b.close)
    layoutb = QVBoxLayout()
    layoutb.addWidget(buttonb)
    b.setLayout(layoutb)
    layouta.addWidget(b)
    
    b.setAttribute(Qt.WA_DeleteOnClose)

    buttona = QPushButton()
    buttona.setText('check')
    buttona.clicked.connect(lambda:check(buttonb))
    layouta.addWidget(buttona)
    
    a.setLayout(layouta)
    a.show()
    app.exec_()

if __name__ == "__main__":
    launchBoard(sys.argv)
    #test(sys.argv)

    