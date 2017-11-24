# -*- coding: utf-8 -*-
"""
Created on Sat Nov 22 22:11:23 2014

@author: thomasdeneux
"""

import win32com.client
_objShell = win32com.client.Dispatch("WScript.Shell")

os_AppDataFolder = _objShell.SpecialFolders("AppData")

