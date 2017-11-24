# -*- coding: utf-8 -*-
"""
Created on Mon Sep 15 22:57:32 2014

@author: THomas
"""

import shutil
import settings

# remove current state folder
shutil.rmtree(settings.SBpath,True)

# but do not remove any cloud content!