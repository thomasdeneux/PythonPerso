# -*- coding: utf-8 -*-
"""
Created on Mon Sep 15 22:56:30 2014

@author: THomas
"""

import sys
import settings, registerfolder, board

c = settings.currentState()
d = sys.argv[1]
alreadyreg = False;
for val in c.folderList.itervalues():
    if val.path==d:
        alreadyreg = True
        break
 
if not alreadyreg:       
    registerfolder.registerFolder(d)
board.launchBoard()
