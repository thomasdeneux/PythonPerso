
# example taken from http://fr.wikibooks.org/wiki/PyQt/Premier_exemple_:_Hello_World_!

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys
if sys.platform=='win32':
    import win32com.client # i have no idea why this one is needed for compiled helloworld.exe to be executed, while it is not needed for helloworld.py to be executed


    
def main(args) :
    #chaque programme doit disposer d'une instance de QApplication gerant l'ensemble des widgets
    app=QApplication(args)
    #un nouveau bouton
    button=QPushButton("Hello World !", None)
    #qu'on affiche
    button.show()
    #fin de l'application lorsque toutes les fenetres sont fermees
    app.connect(app,SIGNAL("lastWindowClosed()"),app,SLOT("quit()"))
    #fin de l'application lorsque l'utilisateur clique sur le bouton
    app.connect(button, SIGNAL("clicked()"),app,SLOT("quit()"))
    #boucle principale de traitement des evenements
    app.exec_()
 


if __name__ == "__main__":
#    installWizard(sys.argv)
    main(sys.argv)