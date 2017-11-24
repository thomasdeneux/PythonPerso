# -*- coding: utf-8 -*-
"""
Created on Sat Sep 13 10:10:00 2014

@author: THomas
"""


from PyQt4.QtGui import *
from PyQt4.QtCore import *

class SBDialog(QDialog): # provides title and icon
    def __init__(self):
        QDialog.__init__(self,None)
#        self.setWindowTitle("Secure Box")
#        icon = QPixmap()
#        icon.load("connect.ico")
#        self.setWindowIcon(QIcon(icon))
        self.setWindowIcon(QIcon(u'connect.ico'))

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    b = SBDialog()
    b.show()
    app.exec_()

