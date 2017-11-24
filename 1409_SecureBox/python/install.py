# -*- coding: utf-8 -*-

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import os.path, sys, time, re, deamon

import settings, crypto, board

_installVar = dict() # global variable, usefull for passing info between functions

class dropboxPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.setTitle("Dropbox");
        self.setSubTitle("Secure Box relies on Dropbox for storing and sharing your encrypted files on the cloud.");

        layout = QVBoxLayout();        
        
        line = QHBoxLayout();
        label = QLabel("Location of Dropbox main folder:") 
        #self.dropboxEdit = QLineEdit();
        #
        #label.setBuddy(self.dropboxEdit)
        self.dropboxEdit = QLabel("");
        button = QPushButton();
        button.setText("...")
        button.clicked.connect(self.locateDropbox)
        self.registerField("dropboxDir",self.dropboxEdit,"text")
        line.addWidget(label)
        line.addWidget(self.dropboxEdit)
        line.addWidget(button)        
        layout.addLayout(line)
        
        self.setLayout(layout)
        
    def locateDropbox(self):
        DB = QFileDialog.getExistingDirectory(self,"Select Dropbox main folder")
        if not os.path.basename(DB)=='Dropbox':
            QMessageBox.warning(None,"Secure Box","'"+DB+"' is not a valid Dropbox main folder.")            
            return
        self.dropboxEdit.setText(DB)
        self.completeChanged.emit()
                

class createKeyPage(QWizardPage):
    def __init__(self):

        QWizardPage.__init__(self)
        self.setTitle("Identity");
        self.setSubTitle("Creating an identity will allow you to synchronize your folders on other devices and share them with other people.");
        # field marking the completion of the page
        self.keyCreated = False;

        layout = QVBoxLayout();        
        
        self.idCreateButton = QRadioButton("I do not have an identity yet. Create one.")
        self.idCreateButton.setChecked(True)
        layout.addWidget(self.idCreateButton)  
               
        self.idExistsButton = QRadioButton("I already created an identity on another device.")
        self.idExistsButton.toggled.connect(self.locateKey)
        self.registerField("idExists",self.idExistsButton);
        layout.addWidget(self.idExistsButton)  
        
        grid = QGridLayout()
        
        label = QLabel("First Name:")
        self.firstNameEdit = QLineEdit()
        label.setBuddy(self.firstNameEdit)
        self.registerField("firstName*",self.firstNameEdit);
        grid.addWidget(label,0,0)
        grid.addWidget(self.firstNameEdit,0,1)        
        
        label = QLabel("Last Name:")
        self.lastNameEdit = QLineEdit()
        label.setBuddy(self.lastNameEdit)
        self.registerField("lastName*",self.lastNameEdit);
        grid.addWidget(label,1,0)
        grid.addWidget(self.lastNameEdit,1,1)        
         
        label = QLabel("Description of this device:")
        self.deviceEdit = QLineEdit()
        label.setBuddy(self.deviceEdit)
        self.registerField("device*",self.deviceEdit);
        grid.addWidget(label,2,0)
        grid.addWidget(self.deviceEdit,2,1)      
        
        layout.addLayout(grid)
        
        self.summary = QLabel("")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        
        self.setLayout(layout)
        
    def initializePage(self): 
        fcloud = os.path.join(self.field("dropboxDir"),settings.cloudIdentityFileBase)
        if os.path.isfile(fcloud):
            fidtmp = os.path.join(settings.SBpath,'private_tmp.id')
            (password,ok) = QInputDialog.getText(None,"Secure Box","Identity file detected: please enter password")
            password = str(password) # convert from unicode string to byte array
            try:
                crypto.decryptFile(open(fcloud,'rb'),open(fidtmp,'wb'),password)
                self.getuserinfo(fidtmp)
                self.idExistsButton.toggled.disconnect(self.locateKey)
                self.idExistsButton.setChecked(True)
                self.idCreateButton.setEnabled(False)                
            except:
                QMessageBox.warning(None,"Secure Box","Failed loading identity file.")            
            if os.path.isfile(fidtmp):
                os.remove(fidtmp)

    def isComplete(self):
        return (self.idCreateButton.isChecked() or self.idExistsButton.isChecked()) and super(createKeyPage,self).isComplete();
        
    def okKey(self):
        self.summary.setText("<i>Your identity is now stored in "+settings.userPrivateIdentityFile+". You will need this file to install Secure Box on other devices. DO NOT SHARE IT WITH ANYBODY, DO NOT PUT IT ON YOUR DROPBOX OR IN OTHER UNSECURED CLOUD STORAGE PLACE</i>")
        self.keyCreated = True
        
    def locateKey(self):
        if self.idExistsButton.isChecked():
            fname = QFileDialog.getOpenFileName(self,"Locate identity file 'private.id'.",filter="private.id")
            if fname=="":
                self.idCreateButton.setChecked(True)
                return
            self.getuserinfo(fname)
        else:
            self.firstNameEdit.setText("")
            self.firstNameEdit.setEnabled(True)
            self.lastNameEdit.setText("")
            self.lastNameEdit.setEnabled(True)
            
    def getuserinfo(self,fname):
        user = settings.importIdentity(fname)
        self.setField("firstName",user.firstname)
        self.firstNameEdit.setEnabled(False)
        self.setField("lastName",user.lastname)
        self.lastNameEdit.setEnabled(False)
        _installVar['ID'] = user.ID
        _installVar['key'] = user.key
        
class installProgressPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.setTitle("Installation under progress");
        self.setSubTitle("");
        
        self.layout = QVBoxLayout()
        
        self.label = QLabel("")
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label)        
                
        self.setLayout(self.layout)
        
    def initializePage(self): 
        QTimer.singleShot(10,self.doInstall)
        
    def reportProgress(self,msg,sleeptime=.2):
        self.label.setText(msg)  
        QCoreApplication.processEvents()   
        time.sleep(sleeptime) # let the user see the message!
        
    def doInstall(self): # THE INSTALLATION OCCURS HERE!
        
        self.reportProgress("Configuration files")        
        settings.init(self.field("dropboxDir"))
        if not self.field("idExists"):
            self.reportProgress("Generate RSA key",0)        
            ID,privatekey,publickey = crypto.genIdentity()
        
        self.reportProgress("Save identity")        
        user = settings.Identity()
        user.firstname = self.field("firstName")
        user.lastname = self.field("lastName")
        user.device = self.field("device")
        if self.field("idExists"):
            user.ID = _installVar['ID']
            user.key = _installVar['key']
            publickey = crypto.derivePublic(user.key)
        else:
            user.ID = re.sub('[^A-Za-z0-9]+', '', user.firstname+user.lastname).lower()+ID
            user.key = privatekey
        user.isprivate = True
        user.export(settings.userPrivateIdentityFile)
        user.key = publickey
        user.isprivate = False
        user.export(settings.userPublicIdentityFile)

        # go to next page
        self.wizard().next()
                
            
class installFinishedPage(QWizardPage):
    def __init__(self):
        QWizardPage.__init__(self)
        self.setTitle("Installation finished");
        self.setSubTitle("");
        
        # Some basic instructions on Secure Box usage     
        txt1 = """
<h3>How to use Secure Box</h3>     
<p>Any folder on your computer can be synchronized with an encrypted version onto the cloud.
<br/>Run Secure Box board to register folders and share them with other people.
<br/>Folders can also be registered from Windows Explorer context menu.</p>"""
        txt2 = """
<h3>Your identity</h3>
<p>Your identity and your private key are saved in file:
<br/><a href=""" + settings.keyFolder + """ style='text-decoration: none; color: black'>
<small>""" + settings.userPrivateIdentityFile + """</small></a>.
<br/>Do not share this file with anybody, do not put it on the cloud either.
To import your identity onto other devices, Secure Box will provide temporary password-protected transfer through the cloud.
"""       
        # Layout 
        self.layout = QVBoxLayout()
        
        # First paragraph
        label = QLabel(txt1)
        label.setWordWrap(True)
        self.layout.addWidget(label)        
                
        # Run board now?
        self.check = QCheckBox();
        self.check.setText("run Secure Box board now")
        self.check.setChecked(False)
        self.registerField("launchBoard",self.check);
        self.layout.addWidget(self.check)

        # Second paragraph
        label = QLabel(txt2)
        label.setWordWrap(True)
        self.layout.addWidget(label)        
                
        self.setLayout(self.layout)
        
    def initializePage(self): 
        # default check the box only if we reached this page
        self.check.setChecked(True)
       
            
class InstallWizard(QWizard):
    def __init__(self):
        QWizard.__init__(self)
        self.addPage(dropboxPage())
        self.addPage(createKeyPage())
        self.addPage(installProgressPage())
        self.addPage(installFinishedPage())
        self.setWindowTitle("Secure Box")
        
    def done(self,res):
        super(QWizard,self).done(res)
        if self.field("launchBoard"):
            board.Board().show()

def installWizard(arg=[]):
    
    app = QApplication(arg)
    wizard = InstallWizard()
    wizard.show();
    app.exec_();


if __name__ == "__main__":
    installWizard(sys.argv)
