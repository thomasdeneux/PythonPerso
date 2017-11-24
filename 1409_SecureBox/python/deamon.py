# -*- coding: utf-8 -*-
"""
Created on Mon Sep 15 15:19:53 2014

@author: THomas
"""

import time

import sync, registerfolder

def deamon():
    # regular synchronization
    print 'REGULAR SYNCHRONIZATION'
    sync.Synchronize()
    
    # check for invitations
    print 'CHECK INVITATIONS'
    registerfolder.joinInvitedFolders()
    
    # check for key requests
    print 'CHECK KEY REQUESTS'
    registerfolder.shareRequestedKeys()
    
    # check for new contacts
    print 'CHECK CONTACTS'
    registerfolder.detectNewContacts()
    
def launchDeamon(sleeptime=10):
    while True:
        try:
            deamon()    
        except:
            pass
        
        # wait
        time.sleep(sleeptime)
    
if __name__ == "__main__":
    deamon()
    
