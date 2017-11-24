# -*- coding: utf-8 -*-

import sip
sip.setapi('QString',2)

from PyQt4.QtGui import *
from PyQt4.QtCore import *
import sys, csv, os, time


import numpy as np
from scipy import misc
if sys.platform=='win32':
    import win32com.client # i have no idea why this one is needed for compiled helloworld.exe to be executed, while it is not needed for helloworld.py to be executed

#from skimage import io as misc

from BLK import *


def interpolate_prepare(imsize, par, offseta=(0,0), offsetr=(0,0)):
    # interpolation grid
    (nxa,nya) = (par['nxa'],par['nya'])
    (nxr,nyr) = (par['nxr'],par['nyr'])
    # (final points positions)
    yy, xx = np.mgrid[0:nyr,0:nxr]
    pp = np.vstack((xx.flatten(),yy.flatten()))
    # (where to interpolate the image)
    theta = par['theta']
    R = np.array([[np.cos(-theta),np.sin(-theta)],[-np.sin(-theta),np.cos(-theta)]])
    S = (1/par['scale'])*np.array([[1,0],[0,-1]]) # includes y flip
    A = np.dot(S,R)      
    centera = np.array([[nxa/2-offseta[0]],[nya/2-offseta[1]]]) # where in the to-be-registered image is the center of the original (before taking an ROI) image
    centerr = np.array([[nxr/2-offsetr[0]+par['x']],[nyr/2-offsetr[1]+par['y']]]) # to which point in the reference image does 'centera' correspond
    pp1 = centera + np.dot(A,pp-centerr)
    x = pp1[0].reshape(nyr,nxr)
    y = pp1[1].reshape(nyr,nxr)
    
    # interpolation parameters
    # (rounding)
    x0 = np.floor(x).astype(int)
    x1 = x0 + 1
    y0 = np.floor(y).astype(int)
    y1 = y0 + 1
    # (clipping)
    x0 = np.clip(x0, 0, imsize[0]-1);
    x1 = np.clip(x1, 0, imsize[0]-1);
    y0 = np.clip(y0, 0, imsize[1]-1);
    y1 = np.clip(y1, 0, imsize[1]-1);

    # weights for interpolation
    wa = (x1-x) * (y1-y)
    wb = (x1-x) * (y-y0)
    wc = (x-x0) * (y1-y)
    wd = (x-x0) * (y-y0)

    return (x0,x1,y0,y1,wa,wb,wc,wd)
    
def interpolate(im, par, offseta=(0,0), offsetr=(0,0)):
    # prepare
    imsize = (im.shape[-1],im.shape[-2])
    (x0,x1,y0,y1,wa,wb,wc,wd) = interpolate_prepare(imsize, par, offseta=(0,0), offsetr=(0,0))

    # interpolation
    Ia = im[..., y0, x0 ]
    Ib = im[..., y1, x0 ]
    Ic = im[..., y0, x1 ]
    Id = im[..., y1, x1 ]

    return wa*Ia + wb*Ib + wc*Ic + wd*Id


def getfiles(msg,filt,doMult=False):
    # base folder
    fsavebasefolder = 'basefolder.txt'
    if os.path.isfile(fsavebasefolder):
        basefolder = str(open(fsavebasefolder).read())
    else:
        basefolder = ''
    # get file(s)
    if doMult:
        fname = QFileDialog.getOpenFileNames(None,msg,directory=basefolder,filter=filt)
        if fname:
            f = fname[0]
        else:
            f = []
    else:
        fname = QFileDialog.getOpenFileName(None,msg,directory=basefolder,filter=filt)
        f = fname
    # set base folder
    if f:
        d = os.path.dirname(f)
        if d != basefolder:
            open(fsavebasefolder,'wt').write(d)

    return fname


def FlipData():
    fnamea = getfiles("Locate data to flip upside-down","*.BLK",True)
    if not fnamea: return

    # init progress viewer
    progress = QProgressDialog()
    progress.setMaximum(len(fnamea))
    progress.setMinimumDuration(0)
    progress.show()
    
    # flip data
    for i in range(len(fnamea)):
        (h,data) = readBLK(fnamea[i])
        data = data[:,:,::-1,:]
        d,base = os.path.split(fnamea[i])
        base,ext = os.path.splitext(base)
        d = os.path.join(d,'flip')
        progress.setLabelText(base)
        progress.setValue(i)
        if not os.path.isdir(d): os.mkdir(d)
        saveBLK(h,data,os.path.join(d,base+'-flip.BLK'))
        progress.setValue(i+.9)
        time.sleep(0.05)
        if progress.wasCanceled(): break # this is not working...

def AlignData():
    # check if there are already saved registration parameters
    fsavepar = 'registration.csv'
    if os.path.isfile(fsavepar):
        par = dict()
        for key, val in csv.reader(open(fsavepar)):
            par[key] = float(val)
    else:
        QMessageBox.warning(None,"Error","Define alignment parameters before aligning data.")            
        return
        
    # get data
    fnamea = getfiles("Locate data to realign","*.BLK",True)
    if not fnamea: return
    fnameref = getfiles("Locate one file from the reference data","*.BLK",False)
    if not fnameref: return
        
    # check sizes
    ha = headBLK(fnamea[0])
    hr = headBLK(fnameref)
    if ha['x2roi']>=par['nxa'] or ha['y2roi']>=par['nya']:
        QMessageBox.warning(None,"Error","data to be realigned is larger than image used for defining alignment parameters!")            
        return
    if hr['x2roi']>=par['nxr'] or hr['y2roi']>=par['nyr']:
        QMessageBox.warning(None,"Error","reference data is larger than reference image used for defining alignment parameters!")            
        return
    
    # init progress viewer
    progress = QProgressDialog()
    progress.setMaximum(len(fnamea))
    progress.setMinimumDuration(0)
    progress.show()
    
    # perform correction
    for i in range(len(fnamea)):
        d,base = os.path.split(fnamea[i])
        base,ext = os.path.splitext(base)
        d = os.path.join(d,'align')
        progress.setLabelText(base)
        progress.setValue(i)
        (h,data) = readBLK(fnamea[i])
        data = interpolate(data,par,(ha['x2roi'],ha['y2roi']),(hr['x2roi'],hr['y2roi']))
        if not os.path.isdir(d): os.mkdir(d)
        saveBLK(h,data,os.path.join(d,base+'-align.BLK'))
        progress.setValue(i+.9)
        time.sleep(0.05)
        if progress.wasCanceled(): break # this is not working...


def SetAlignmentParameters():
    fnamea = getfiles("Locate image for data to be realigned","*.BMP")
    if not fnamea: return
    fnameref  = getfiles("Locate reference image","*.BMP")
    if not fnameref: return

    x = misc.imread(fnamea)
    ref = misc.imread(fnameref)
    
    b = RegistrationBoard(x,ref)
    b.show()
    return b # avoid destroying b!
 
class OpenWindows:
    curset = []

class StartupDialog(QDialog):
    
    def __init__(self,ws):
        self.ws = ws # OpenWindows object keeps reference of opened windows
        QDialog.__init__(self,None)
        # grid layout
        grid = QGridLayout()
        self.setLayout(grid)
        # buttons
        button = QPushButton()
        grid.addWidget(button,1,1)
        button.setText('FLIP DATA')
        button.clicked.connect(lambda:self.action('flip'))
        button = QPushButton()
        grid.addWidget(button,1,2)
        button.setText('ALIGN DATA')
        button.clicked.connect(lambda:self.action('align'))
        button = QPushButton()
        grid.addWidget(button,1,3)
        button.setText('DEFINE ALIGNMENT PARAMETERS')
        button.clicked.connect(lambda:self.action('register'))
    
    def action(self,flag):
        if flag=='flip':
            FlipData()
        elif flag=='align':
            AlignData()
        elif flag=='register':
            board = SetAlignmentParameters()
            self.ws.curset.append(board) # keep a reference on board to keep it open (note that self.ws object lives in the main() function so it is not deleted when StartDialog object is deleted)
        #self.close()
        

class RegistrationBoard(QDialog):
    a = []
    ref = []
    par = {'nxa':0, 'nya':0, 'nxr':0, 'nyr':0, 'x':0, 'y':0, 'theta':0, 'scale':1}
    fsavepar = 'registration.csv'
    px0 = []
    py0 = []
    parx0 = []
    pary0 = []
    movefast = True
    
    def __init__(self,a,ref):
        QDialog.__init__(self,None)
        
        # use a subcontainer to easily reset the display
        mainlayout = QHBoxLayout()
        self.setLayout(mainlayout)
        
        # controls
        self.controlspanel = QWidget()
        mainlayout.addWidget(self.controlspanel)
        self.initcontrols()        
        
        # image
        self.imagepanel = QLabel()
        mainlayout.addWidget(self.imagepanel)
        
        # display image
        self.setdata(a,ref)
        self.showimage()
        
    def initcontrols(self):
        vlayout = QVBoxLayout()
        self.controlspanel.setLayout(vlayout)
        
        # some text
        label = QLabel()
        vlayout.addWidget(label)
        p1='<p style="font-weight:bold; font-size:xx-large">Manual registration</p>'
        p2='<p style="font-size:x-large">Use mouse and keyboard to move/rotate/scale the image until it matches the reference image, then press DONE.</p>'
        label.setText(p1+p2)
        label.setWordWrap(True)
        
        # keyboard graphic help
        label = QLabel()
        vlayout.addWidget(label)
        label.setPixmap(QPixmap('keyboard.png'))
        
        # Save button
        button = QPushButton()
        vlayout.addWidget(button)
        button.setText("DONE")
        button.clicked.connect(lambda:self.finish())

        # spacer to fill extra space in the bottom
        vlayout.addStretch()
        
    def setdata(self,a,ref):
        # transform images to z-scores
        ar = a.reshape(-1);
        self.a = ((ar-ar.mean())/ar.std()).reshape(a.shape) # z-score
        rr = ref.reshape(-1);
        self.ref = ((rr-rr.mean())/rr.std()).reshape(ref.shape) # z-score
        
        #        # define the colormap
        #        self.colortable = [qRgb(i, i, 255-i) for i in range(128)]+[qRgb(255, 255-i, 0) for i in range(128)]
        
        # check if there are already saved registration parameters
        if os.path.isfile(self.fsavepar):
            for key, val in csv.reader(open(self.fsavepar)):
                self.par[key] = float(val)
        
        # images sizes
        (self.par['nya'],self.par['nxa']) = a.shape
        (self.par['nyr'],self.par['nxr']) = ref.shape

        
    def showimage(self):
        # interpolate
        a1 = interpolate(self.a,self.par)
        
        # display
        im = self.ref-a1
        #        (m,M) = (im.min(),im.max())
        (m,M) = (-2,2)
        im = np.int8(255*(im.clip(m,M)-m)/(M-m))
        qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
        #        qim.setColorTable(self.colortable)
        qim = QPixmap.fromImage(qim)   
        self.imagepanel.setPixmap(qim)
        

    def mousePressEvent(self,evnt):
        self.px0 = evnt.x()
        self.py0 = evnt.y()
        self.parx0 = self.par['x']
        self.pary0 = self.par['y']
        
    def mouseMoveEvent(self,evnt):
        self.par['x'] = self.parx0+(evnt.x()-self.px0)
        self.par['y'] = self.pary0+(evnt.y()-self.py0)
        self.showimage()
        
    def keyPressEvent(self,evnt):
        key = evnt.key()
        if self.movefast:
            a = 10
        else:
            a = 1
        if key==81: # q
            self.movefast = not self.movefast
        elif key==16777234 or key==52: # left
            self.par['x'] = self.par['x']-a;
        elif key==16777236 or key==54: # right
            self.par['x'] = self.par['x']+a;
        elif key==16777235 or key==56: # up
            self.par['y'] = self.par['y']-a;
        elif key==16777237 or key==50: # down
            self.par['y'] = self.par['y']+a;
        elif key==65: # a
            self.par['theta'] = self.par['theta']+a*np.pi/900; # rotation by 2/0.2 degree
        elif key==83: # s        
            self.par['scale'] = self.par['scale']/np.power(1.002,a); 
        elif key==68: # d
            self.par['theta'] = self.par['theta']-a*np.pi/900; # rotation by 2/0.2 degree
        elif key==87: # w
            self.par['scale'] = self.par['scale']*np.power(1.002,a); 
        else:
            #            print key
            return
        self.showimage()
    
    def finish(self):
        # save parameters
        w = csv.writer(open(self.fsavepar, "w"))
        for key,val in self.par.iteritems():
            w.writerow([key,val])
        # close window
        self.close()
        
    
def main(args) :
    ws = OpenWindows() # keep references of windows that we want to keep open
    app=QApplication([''])
    d = StartupDialog(ws)
    d.show()
    app.exec_()



if __name__ == "__main__":
    main(sys.argv)


