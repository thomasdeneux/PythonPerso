import os, shutil, sys
from datetime import datetime

import settings, crypto
        

###################### FILE OPERATIONS ########################################


def modifyName(file):
    (file, ext) = os.path.splitext(file)
    timestamp = datetime.today().strftime('%d-%m-%y, %H-%M-%S')
    return file+' - conflict '+timestamp+ext

def GetFingerPrint(file):
    t = os.path.getmtime(file)
    t = round(t*1000)/1000 # round to the ms to avoid comparisons to be flawn by numerical precision errors
    return t
 
def CopyStat(file,file0):
    if os.path.isdir(file):        
        if not os.path.isdir(file0):
            os.mkdir(file0)
    else:
        open(file0,'w').close()
    shutil.copystat(file,file0)
        
def Encrypt(file1,file2,folderkey):
    if os.path.isdir(file1):        
        if not os.path.isdir(file2):
            if os.path.isfile(file2): os.remove(file2)
            os.mkdir(file2)
    else:
        crypto.encryptFile(open(file1,'rb'),open(file2,'wb'),folderkey)
    shutil.copystat(file1,file2)
  
def Decrypt(file2,file1,folderkey):
    if os.path.isdir(file2):        
        if not os.path.isdir(file1):
            if os.path.isfile(file1): os.remove(file1)
            os.mkdir(file1)
    else:
        crypto.decryptFile(open(file2,'rb'),open(file1,'wb'),folderkey)
    shutil.copystat(file2,file1)

def MoveFile(file,filenew):
    os.rename(file,filenew)
    
def Remove(file):
    if os.path.isdir(file):
        shutil.rmtree(file,True) 
    else:
        os.remove(file)

###################### SPECIAL FOLDER ICON ####################################

def MakeSpecialIcon(d):
    inifile = os.path.join(d,'desktop.ini')
    if os.path.isfile(inifile):
        return
    f = open(inifile,'w')
    txt = '[.ShellClassInfo]\nIconResource='+os.path.join(os.getcwd(),'synchronizedFolderIcon.ico')+',0'
    f.write(txt)
    f.close()
    os.system('attrib +s "'+d+'"') # set the 'system' attribute, that will result in the desktop.ini file to be read
    
###################### SYNCHRONIZATION ########################################

  
def InspectFolders(State,Source,Syncro,folderkey):
    list0 = os.listdir(State)
    list1 = os.listdir(Source)
    list2 = os.listdir(Syncro)
    set0 = set(list0); set1 = set(list1); set2 = set(list2)
    SET = set0 | set1 | set2
    LIST = list(SET)
    
    # Make Special Icon for the Source folder
    MakeSpecialIcon(Source)
    
    # loop on files/folders
    anymod1, anymod2 = False, False
    for f1 in LIST:
        try:
            # do not synchronize desktop.ini files
            if f1.lower() == "desktop.ini":
                continue
        
            # diagnosis?
            in0 = f1 in set0
            in1 = f1 in set1
            in2 = f1 in set2
            file0 = os.path.join(State,f1)
            file1 = os.path.join(Source,f1)
            file2 = os.path.join(Syncro,f1)
            if in0: 
                t0 = GetFingerPrint(file0)
            if in1: 
                d1 = os.path.isdir(file1)
                t1 = GetFingerPrint(file1)
            if in2: 
                d2 = os.path.isdir(file2)
                t2 = GetFingerPrint(file2)
            chg1 = in1 and ((not in0) or (in0 and t1!=t0))
            chg2 = in2 and ((not in0) or (in0 and t2!=t0))
            conflict = chg1 and chg2 and not ((d1 and d2) or (not d1 and not d2 and t1==t2))
            rm1 = not in1 and in0
            rm2 = not in2 and in0
            
            # if there is a conflict, resolve it by synchronizing the local file with a modified name
            if conflict:
                f1mod = modifyName(f1)
                print('Handle conflict: add '+f1mod+' from Local, keep '+f1+' from Server')
                file0mod = os.path.join(State,f1mod)
                file1mod = os.path.join(Source,f1mod)
                file2mod = os.path.join(Syncro,f1mod)
                MoveFile(file1,file1mod)
                CopyStat(file1mod,file0mod)
                Encrypt(file1mod,file2mod,folderkey)
                if d1: InspectFolders(file0mod,file1mod,file2mod,folderkey)
                anymod1 = True;
                chg1 = False # f1 has not been modified any more, it is f1mod that has been created
                
            # synchronize without fear of a conflict
            if chg1: 
                print('Add/Change '+f1+' from Local')
                CopyStat(file1,file0)
                Encrypt(file1,file2,folderkey)
                if d1: InspectFolders(file0,file1,file2,folderkey)
                anymod2 = True;
            elif chg2:
                print('Add/Change '+f1+' from Server')
                CopyStat(file2,file0)
                Decrypt(file2,file1,folderkey)
                if d2: InspectFolders(file0,file1,file2,folderkey)
                anymod1 = True;
            elif rm1:
                print(f1+' removed in Local')
                Remove(file0)
                if in2: Remove(file2)
            elif rm2:
                print(f1+' removed in Server')
                Remove(file0)
                Remove(file1)
            elif d1:
                # need to get inside folders, because if only the content of some subfolders has changed, the modification date of the folder was not updated
                InspectFolders(file0,file1,file2,folderkey)
                
        except:
            print("encountered an error!")
            print(sys.exc_info())
            
    # Set appropriate modification times to folders
    if anymod1 and anymod2:
        t = os.path.getmtime(State) # State was modified during this sync
        os.utime(Source,(t, t))
        os.utime(Syncro,(t, t))
    elif anymod1:
        t = os.path.getmtime(Syncro) # Syncro was not modified during this sync
        os.utime(State,(t, t))
        os.utime(Source,(t, t))
    elif anymod2:
        t = os.path.getmtime(Source) # Source was not modified during this sync
        os.utime(State,(t, t))
        os.utime(Syncro,(t, t))
                                    

def Synchronize():
    dropboxDir = settings.config().dropboxDir;
    folderList = settings.currentState().folderList;
    
    for (key,val) in folderList.iteritems():
        Source = val.path;
        if not os.path.isdir(Source): 
            print 'no source'
            continue
        Syncro = os.path.join(dropboxDir,settings.SBFolderBase+val.ID,settings.FilesFolderBase)
        if not os.path.isdir(Syncro): 
            print 'no syncro: missing folder '+Syncro
            continue
        State = os.path.join(settings.syncStateFolder,val.ID)
        if not os.path.isdir(State): 
            print 'no state'
            continue
        InspectFolders(State,Source,Syncro,val.key)
            

############################ MAIN ###############################################
#
## global variables
#mypassword = 'securebox'
#doEncodeFileName = False
#doEncodeFolderName = False
#
## main function
#def main():
#    global doEncodeFileName, doEncodeFolderName
#        
#    if not os.path.isfile('config.csv'):
#        app = wx.App(0) 
#        wx.MessageDialog(None,"Run 'configure' first",'securebox',wx.OK|wx.ICON_ERROR).ShowModal()
#        return
#    
#    # Read options
#    options = {}
#    for key, val in csv.reader(open("config.csv")):
#        options[key] = val
#    
#    print os.getcwd()
#    print options
#    
#    doEncodeFileName = options['encodeFileName']=='True'
#    doEncodeFolderName = options['encodeFolderName']=='True'
#    print doEncodeFileName
#    
#    
#    StateDir = os.path.join(os.getcwd(),'currentstate')
#    if not os.path.isdir(StateDir): os.mkdir(StateDir)
#    SourceDir = options['Source']
#    SyncroDir = options['Syncro']
#    
#    # Synchronize every 10 seconds
#    while True: 
#        print ' '
#        try:
#            InspectFolders(StateDir,SourceDir,SyncroDir)
#        except:
#            print 'ERROR'
#            time.sleep(5)
#        time.sleep(10)
#    
#
## Call main function
#main()


if __name__ == "__main__":
    Synchronize()
    