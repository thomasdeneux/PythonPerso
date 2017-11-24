# -*- coding: utf-8 -*-

import numpy as np
from PyQt4.QtGui import *
from PyQt4.QtCore import *

def headBLK(fid):
    if not hasattr(fid, 'read'):
        fid = open(fid,'rb')
    h = dict();

    # DATA INTEGRITY 		####################################
    h['filesize']              =np.fromfile(fid,np.int32,1)[0];
    h['checksum_header']			=np.fromfile(fid,np.int32,1)[0];
    	# beginning with the lLen Header field
    
    h['checksum_data']			=np.fromfile(fid,np.int32,1)[0];
    
    # COMMON TO ALL DATA FILES 	####################################
    h['lenheader']			=np.fromfile(fid,np.int32,1)[0];
    h['versionid']			=np.fromfile(fid,np.float32,1)[0];
    h['filetype']			=np.fromfile(fid,np.int32,1)[0];
    	# RAWBLOCK_FILE          (11)
    	# DCBLOCK_FILE           (12)
    	# SUM_FILE               (13)
    
    h['filesubtype']			=np.fromfile(fid,np.int32,1)[0];
    	# FROM_VDAQ              (11)
    	# FROM_ORA               (12)
    	# FROM_DYEDAQ            (13)
    
    h['datatype']			=np.fromfile(fid,np.int32,1)[0];
    	# DAT_UCHAR     (11)
    	# DAT_USHORT    (12)
    	# DAT_LONG      (13)
    	# DAT_FLOAT     (14)
    
    h['sizeof']				=np.fromfile(fid,np.int32,1)[0];
    	# e.g. sizeof(long), sizeof(float)
    
    h['framewidth']			=np.fromfile(fid,np.int32,1)[0];
    h['frameheight']			=np.fromfile(fid,np.int32,1)[0];
    h['nframesperstim']			=np.fromfile(fid,np.int32,1)[0];
    h['nstimuli']			=np.fromfile(fid,np.int32,1)[0];
    h['initialxbinfactor']		=np.fromfile(fid,np.int32,1)[0];
    	# from data acquisition
    h['initialybinfactor']		=np.fromfile(fid,np.int32,1)[0];
    	# from data acquisition
    
    h['xbinfactor']			=np.fromfile(fid,np.int32,1)[0];
    	# this file
    h['ybinfactor']			=np.fromfile(fid,np.int32,1)[0];
    	# this file
    
    h['username']			=str(fid.read(32));
    h['recordingdate']			=str(fid.read(16));
    h['x1roi']				=np.fromfile(fid,np.int32,1)[0];
    h['y1roi']				=np.fromfile(fid,np.int32,1)[0];
    h['x2roi']				=np.fromfile(fid,np.int32,1)[0];
    h['y2roi']				=np.fromfile(fid,np.int32,1)[0];
    
    # LOCATE DATA AND REF FRAMES 	####################################
    h['stimoffs']			=np.fromfile(fid,np.int32,1)[0];
    h['stimsize']			=np.fromfile(fid,np.int32,1)[0];
    h['frameoffs']			=np.fromfile(fid,np.int32,1)[0];
    h['framesize']			=np.fromfile(fid,np.int32,1)[0];
    h['refoffs']				=np.fromfile(fid,np.int32,1)[0];
    h['refsize']				=np.fromfile(fid,np.int32,1)[0];
    h['refwidth']			=np.fromfile(fid,np.int32,1)[0];
    h['refheight']			=np.fromfile(fid,np.int32,1)[0];
    
    # Common to data files that have undergone some form of
    # "compression" or "summing"
    # i.e. The data in the current file may be the result of
    #      having summed blocks 'a'-'f', frames 1-7
    h['whichblocks']			=np.fromfile(fid,np.uint16,16);
    h['whichframes']			=np.fromfile(fid,np.uint16,16);
    
    # DATA ANALYSIS			####################################
    h['loclip']				=np.fromfile(fid,np.int32,1)[0];
    h['hiclip']				=np.fromfile(fid,np.int32,1)[0];
    h['lopass']				=np.fromfile(fid,np.int32,1)[0];
    h['hipass']				=np.fromfile(fid,np.int32,1)[0];
    h['operationsperformed']		=str(fid.read(64));
    
    # ORA-SPECIFIC			####################################
    h['magnification']			=np.fromfile(fid,np.float32,1)[0];
    h['gain']				=np.fromfile(fid,np.uint16,1)[0];
    h['wavelen']			=np.fromfile(fid,np.uint16,1)[0];
    h['exposuretime']			=np.fromfile(fid,np.int32,1)[0];
    h['nrepetitions']			=np.fromfile(fid,np.int32,1)[0];
    h['acquisitiondelay']		=np.fromfile(fid,np.int32,1)[0];
    h['interstiminterval']		=np.fromfile(fid,np.int32,1)[0];
    h['creationdate']			=str(fid.read(16));
    h['datafilename']			=str(fid.read(64));
    h['orareserved']			=str(fid.read(256));
    
    
    if h['filesubtype'] == 13:   #it's dyedaq file
      
        #  OIHEADER.H
        #  last revised 4.5.97 by Chaipi Wijnbergen for DyeDaq
        #  
        #  DyeDaq-specific
        h['includesrefframe']    =np.fromfile(fid,np.int32,1)[0];     # 0 or 1
        temp                =str(fid.read(128));
        h['listofstimuli']       =temp; # temp(1:max(find(temp!=0)));  # up to first non-zero stimulus
        h['ntrials']             =np.fromfile(fid,np.int32,1)[0];
        h['scalefactor']         =np.fromfile(fid,np.int32,1)[0];          # bin * trials
        h['cameragain']          =np.fromfile(fid,np.int16,1)[0];         # shcameragain        1,   2,   5,  10
        h['ampgain']             =np.fromfile(fid,np.int16,1)[0];            # amp gain            1,   4,  10,  16,
                                                 #                    40,  64, 100, 160,
                                                 #                    400,1000
        h['samplingrate']        =np.fromfile(fid,np.int16,1)[0];       # sampling rate (1/x)
                                                 #                     1,   2,   4,   8,
                                                 #                     16,  32,  64, 128,
                                                 #                     256, 512,1024,2048
        h['average']             =np.fromfile(fid,np.int16,1)[0];            # average             1,   2,   4,   8,
                                                 #                    16,  32,  64, 128
        h['exposuretime']        =np.fromfile(fid,np.int16,1)[0];       # exposure time       1,   2,   4,   8,
                                                 #                    16,  32,  64, 128,
                                                 #                    256, 512,1024,2048
        h['samplingaverage']     =np.fromfile(fid,np.int16,1)[0];    # sampling average    1,   2,   4,   8,
                                                 #                    16,  32,  64, 128
        h['presentaverage']      =np.fromfile(fid,np.int16,1)[0];
        h['framesperstim']       =np.fromfile(fid,np.int16,1)[0];
        h['trialsperblock']      =np.fromfile(fid,np.int16,1)[0];
        h['sizeofanalogbufferinframes'] =np.fromfile(fid,np.int16,1)[0];
        h['cameratrials']        =np.fromfile(fid,np.int16,1)[0];
        h['filler']              =str(fid.read(106));
      
        h['dyedaqreserved']      =str(fid.read(256));
    else:   # it's not dyedaq specific
    
        # VDAQ-SPECIFIC			####################################
        h['includesrefframe']		=np.fromfile(fid,np.int32,1)[0];
        h['listofstimuli']			=str(fid.read(256));
        h['nvideoframesperdataframe']	=np.fromfile(fid,np.int32,1)[0];
        h['ntrials']				=np.fromfile(fid,np.int32,1)[0];
        h['scalefactor']			=np.fromfile(fid,np.int32,1)[0];
        h['meanampgain']			=np.fromfile(fid,np.float32,1)[0];
        h['meanampdc']			=np.fromfile(fid,np.float32,1)[0];
        h['vdaqreserved']			=str(fid.read(256));
    
    # USER-DEFINED			####################################
    h['user']				=str(fid.read(256));
    
    # COMMENT			####################################
    h['comment']				=str(fid.read(256));
    h['refscalefactor']          =np.fromfile(fid,np.int32,1)[0];          # bin * trials for reference
    
    ##################  END DEFINITIONS OF VARIABLES  ##################
    
    # Note that doing ftell(fid) here results in h['lenheader + 4!!, which means
    # that we read one extra int32!!! But which one...?
    
    #fseek(fid,0,1);            # go to EOF
    #h['actuallen=ftell(fid);   # report where EOF is in bytes
    
    return h
    

def writeheader(s,fid):
    # WARNING: all fields in s must be already at the appropriate format (int8, float32, ...), as they will be saved 'as they are' to the file
    
    ################## BEGIN DEFINITIONS OF VARIABLES ##################
    
    # Note: we save char as uint8, because some special Matlab char type seems
    # strange with values actually from 0 to 65535, all those <256 being
    # written by fwrite with only one byte, but all those >255 being written
    # with 2 bytes!!
    
    err = False
    
    # DATA INTEGRITY ####################################
    np.array(s['filesize'],dtype='int32').tofile(fid)
    np.array(s['checksum_header'],dtype='int32').tofile(fid)
    # beginning with the lLen Header field
    
    np.array(s['checksum_data'],dtype='int32').tofile(fid)
    
    # COMMON TO ALL DATA FILES ####################################
    np.array(s['lenheader'],dtype='int32').tofile(fid)
    np.array(s['versionid'],dtype='float32').tofile(fid)
    np.array(s['filetype'],dtype='int32').tofile(fid)
    # RAWBLOCK_FILE          (11)
    # DCBLOCK_FILE           (12)
    # SUM_FILE               (13)
    
    np.array(s['filesubtype'],dtype='int32').tofile(fid)
    # FROM_VDAQ              (11)
    # FROM_ORA               (12)
    # FROM_DYEDAQ            (13)
    
    np.array(s['datatype'],dtype='int32').tofile(fid)
    # DAT_UCHAR     (11)
    # DAT_USHORT    (12)
    # DAT_LONG      (13)
    # DAT_FLOAT     (14)
    
    np.array(s['sizeof'],dtype='int32').tofile(fid)
    # e.g. sizeof(long)'],dtype= sizeof(float)
    
    np.array(s['framewidth'],dtype='int32').tofile(fid)
    np.array(s['frameheight'],dtype='int32').tofile(fid)
    np.array(s['nframesperstim'],dtype='int32').tofile(fid)
    np.array(s['nstimuli'],dtype='int32').tofile(fid)
    np.array(s['initialxbinfactor'],dtype='int32').tofile(fid)
    # from data acquisition
    np.array(s['initialybinfactor'],dtype='int32').tofile(fid)
    # from data acquisition
    
    np.array(s['xbinfactor'],dtype='int32').tofile(fid)
    # this file
    np.array(s['ybinfactor'],dtype='int32').tofile(fid)
    # this file
    
    fid.write(bytearray(s['username'])+bytearray(32-len(s['username'])))
    fid.write(bytearray(s['recordingdate'])+bytearray(16-len(s['recordingdate'])))
    np.array(s['x1roi'],dtype='int32').tofile(fid)
    np.array(s['y1roi'],dtype='int32').tofile(fid)
    np.array(s['x2roi'],dtype='int32').tofile(fid)
    np.array(s['y2roi'],dtype='int32').tofile(fid)
    
    # LOCATE DATA AND REF FRAMES ####################################
    np.array(s['stimoffs'],dtype='int32').tofile(fid)
    np.array(s['stimsize'],dtype='int32').tofile(fid)
    np.array(s['frameoffs'],dtype='int32').tofile(fid)
    np.array(s['framesize'],dtype='int32').tofile(fid)
    np.array(s['refoffs'],dtype='int32').tofile(fid)
    np.array(s['refsize'],dtype='int32').tofile(fid)
    np.array(s['refwidth'],dtype='int32').tofile(fid)
    np.array(s['refheight'],dtype='int32').tofile(fid)
    
    # Common to data files that have undergone some form of
    # "compression" or "summing"
    # i.e. The data in the current file may be the result of
    #      having summed blocks 'a'-'f', frames 1-7
    if len(s['whichblocks'])!=16: err=True
    np.array(s['whichblocks'],dtype='uint16').tofile(fid)
    if len(s['whichframes'])!=16: err=True
    np.array(s['whichframes'],dtype='uint16').tofile(fid)
    
    # DATA ANALYSIS####################################
    np.array(s['loclip'],dtype='int32').tofile(fid)
    np.array(s['hiclip'],dtype='int32').tofile(fid)
    np.array(s['lopass'],dtype='int32').tofile(fid)
    np.array(s['hipass'],dtype='int32').tofile(fid)
    
    fid.write(bytearray(s['operationsperformed'])+bytearray(64-len(s['operationsperformed'])))
    
    # ORA-SPECIFIC####################################
    np.array(s['magnification'],dtype='float32').tofile(fid)
    np.array(s['gain'],dtype='uint16').tofile(fid)
    np.array(s['wavelen'],dtype='uint16').tofile(fid)
    np.array(s['exposuretime'],dtype='int32').tofile(fid)
    np.array(s['nrepetitions'],dtype='int32').tofile(fid)
    np.array(s['acquisitiondelay'],dtype='int32').tofile(fid)
    np.array(s['interstiminterval'],dtype='int32').tofile(fid)
    fid.write(bytearray(s['creationdate'])+bytearray(16-len(s['creationdate'])))
    fid.write(bytearray(s['datafilename'])+bytearray(64-len(s['datafilename'])))
    fid.write(bytearray(s['orareserved'])+bytearray(256-len(s['orareserved'])))
    
    
    if s['filesubtype'] == 13:   #it's dyedaq file
      
      #  OIHEADER.H
      #  last revised 4.5.97 by Chaipi Wijnbergen for DyeDaq
      #  
      #  DyeDaq-specific
      np.array(s['includesrefframe'],dtype='int32').tofile(fid)     # 0 or 1
      fid.write(bytearray(s['listofstimuli'])+bytearray(128-len(s['listofstimuli'])))
      np.array(s['ntrials'],dtype='int32').tofile(fid)
      np.array(s['scalefactor'],dtype='int32').tofile(fid)          # bin * trials
      np.array(s['cameragain'],dtype='short').tofile(fid)         # shcameragain        1,   2,   5,  10
      np.array(s['ampgain'],dtype='short').tofile(fid)            # amp gain            1,   4,  10,  16,
                                                 #                    40,  64, 100, 160,
                                                 #                    400,1000
      np.array(s['samplingrate'],dtype='short').tofile(fid)       # sampling rate (1/x)
                                                 #                     1,   2,   4,   8,
                                                 #                     16,  32,  64, 128,
                                                 #                     256, 512,1024,2048
      np.array(s['average'],dtype='short').tofile(fid)            # average             1,   2,   4,   8,
                                                 #                    16,  32,  64, 128
      np.array(s['exposuretime'],dtype='short').tofile(fid)       # exposure time       1,   2,   4,   8,
                                                 #                    16,  32,  64, 128,
                                                 #                    256, 512,1024,2048
      np.array(s['samplingaverage'],dtype='short').tofile(fid)    # sampling average    1,   2,   4,   8,
                                                 #                    16,  32,  64, 128
      np.array(s['presentaverage'],dtype='short').tofile(fid)
      np.array(s['framesperstim'],dtype='short').tofile(fid)
      np.array(s['trialsperblock'],dtype='short').tofile(fid)
      np.array(s['sizeofanalogbufferinframes'],dtype='short').tofile(fid)
      np.array(s['cameratrials'],dtype='short').tofile(fid)
      fid.write(bytearray(s['filler'])+bytearray(106-len(s['filler'])))
      fid.write(bytearray(s['dyedaqreserved'])+bytearray(256-len(s['dyedaqreserved'])))

    else:   # it's not dyedaq specific
    
      # VDAQ-SPECIFIC####################################
      np.array(s['includesrefframe'],dtype='int32').tofile(fid)
      fid.write(bytearray(s['listofstimuli'])+bytearray(256-len(s['listofstimuli'])))
      np.array(s['nvideoframesperdataframe'],dtype='int32').tofile(fid)
      np.array(s['ntrials'],dtype='int32').tofile(fid)
      np.array(s['scalefactor'],dtype='int32').tofile(fid)
      np.array(s['meanampgain'],dtype='float32').tofile(fid)
      np.array(s['meanampdc'],dtype='float32').tofile(fid)
      fid.write(bytearray(s['vdaqreserved'])+bytearray(256-len(s['vdaqreserved'])))
    
    # USER-DEFINED####################################
    fid.write(bytearray(s['user'])+bytearray(256-len(s['user'])))
    
    # COMMENT####################################
    fid.write(bytearray(s['comment'])+bytearray(256-len(s['comment'])))
    np.array(s['refscalefactor'],dtype='int32').tofile(fid)          # bin * trials for reference
    
    ##################  END DEFINITIONS OF VARIABLES  ##################
    
    if err:
        QMessageBox.warning(None,"error while saving block file","Error whils saving block file: Uncorrect headers.")            
        
    
    # Doing ftell(fid) here results in the same as when reading a file with
    # oi_headBLK. But there is the same err=True (see end of oi_headBLK code),
    # which is that it is 4 bytes more than np.array(s.lenheader!!!
    
def readBLK(fname):
    # open file
    fid = open(fname,'rb')
    
    # read header info
    h = headBLK(fid)
    
    # relevant information for reading data
    (nstim,ni,nj,nfr) = (h['nstimuli'],h['framewidth'],h['frameheight'],h['nframesperstim'])
    (lenh,framesize,dtype) = (h['lenheader'],h['framesize'],h['datatype'])
    if dtype==11:
        nbytes = 1
        datatype = np.uint8
    elif dtype==12:
        nbytes = 2
        datatype = np.uint16
    elif dtype==13:
        nbytes = 4;
        datatype = np.uint32
    elif dtype==14:
        nbytes = 4;
        datatype = np.float32
    else:
        print 'error: type unkown'
    if framesize!=ni*nj*nbytes:
        print 'BAD HEADER!!! framesize does not match framewidth*frameheight*nbytes!'
        framesize = ni*nj*nbytes;

    # read data
    fid.seek(lenh)
    data = np.fromfile(fid,datatype,ni*nj*nfr*nstim).reshape((nstim,nfr,nj,ni)) 

    return (h,data)

#def openreadBLK(fname):
#    # open file
#    fid = open(fname,'rb')
#    
#    # read header info
#    h = headBLK(fid)
#    
#    # relevant information for reading data
#    (ni,nj) = (h['framewidth'],h['frameheight'])
#    (lenh,framesize,dtype) = (h['lenheader'],h['framesize'],h['datatype'])
#    if dtype==11:
#        nbytes = 1
#        datatype = np.uint8
#    elif dtype==12:
#        nbytes = 2
#        datatype = np.uint16
#    elif dtype==13:
#        print 'warning: reading longs as ulongs'
#        nbytes = 4;
#        datatype = np.uint32
#    elif dtype==14:
#        nbytes = 4;
#        datatype = np.float32
#    else:
#        print 'error: type unkown'
#    if framesize!=ni*nj*nbytes:
#        print 'BAD HEADER!!! framesize does not match framewidth*frameheight*nbytes!'
#        framesize = ni*nj*nbytes;
#
#    # gather relevant information
#    info = (fid,lenh,framesize,datatype,ni,nj)
#    nframes = h['nstimuli']*h['nframesperstim']
#    return (info,h,nframes)    
#
#def readframe(info,i):
#    (fid,lenh,framesize,datatype,ni,nj) = info
#    # read data
#    fid.seek(lenh+i*framesize)
#    return np.fromfile(fid,datatype,ni*nj).reshape((nj,ni)) 
    

def saveBLK(h,data,fname):
    # open file
    fid = open(fname,'wb')

    # modify header info to match data size
    data = np.array(data,ndmin=4) # make data 4D
    (h['nstimuli'],h['nframesperstim'],h['frameheight'],h['framewidth']) = data.shape
    if data.dtype=='uint8':    
        h['datatype'] = 11
        h['sizeof'] = 1
    elif data.dtype=='uint16':      
        h['datatype'] = 12
        h['sizeof'] = 2
    elif data.dtype=='uint32':     
        h['datatype'] = 13
        h['sizeof'] = 4
    elif data.dtype=='float32':     
        h['datatype'] = 14
        h['sizeof'] = 4
    elif data.dtype=='float64':   
        data = data.astype('float32')
        h['datatype'] = 14
        h['sizeof'] = 4
    else:
        QMessageBox.warning(None,"error","Error: data type "+str(data.dtype)+" cannot be saved to BLK file.")            
    h['framesize'] = h['frameheight']*h['framewidth']*h['sizeof']
    h['filesize'] = h['lenheader']+h['nstimuli']*h['nframesperstim']*h['framesize']        
    
    # save header info
    writeheader(h,fid)
    
    # save data
    fid.seek(h['lenheader'])
    data.tofile(fid)
    
    return

#def openwriteBLK(fname,h,nx,ny,datatype):
#    # open file
#    fid = open(fname,'wb')
#    
#    # modify header info to match data size
#    (h['frameheight'],h['framewidth']) = (ny,nx)
#    if datatype=='uint8':    
#        h['datatype'] = 11
#        h['sizeof'] = 1
#    elif datatype=='uint16':      
#        h['datatype'] = 12
#        h['sizeof'] = 2
#    elif datatype=='uint32':     
#        h['datatype'] = 13
#        h['sizeof'] = 4
#    elif datatype=='float32':     
#        h['datatype'] = 14
#        h['sizeof'] = 4
#    else:
#        QMessageBox.warning(None,"error","Error: data type "+data.dtype+" cannot be saved to BLK file.")            
#    h['framesize'] = h['frameheight']*h['framewidth']*h['sizeof']
#    h['filesize'] = h['lenheader']+h['nstimuli']*h['nframesperstim']*h['framesize']        
#    
#    # save header info
#    writeheader(h,fid)
#    
#    # gather relevant info
#    info = (fid,h['lenheader'],h['framesize'])
#    
#    return info  
#
#def writeframe(info,i,data):
#    (fid,lenh,framesize) = info
#    # write to file
#    fid.seek(lenh+i*framesize)
#    data.tofile(fid)



   
if __name__ == "__main__":
    fname = u'C:\\Users\\THomas\\PROJECTS\\1409_OI\\data\\dualcam\\4ThomasMaster\\led_E1B1.BLK'
    (header,data) = readBLK(fname)
    fsave = u'C:\\Users\\THomas\\PROJECTS\\1409_OI\\data\\dualcam\\testsave.BLK'
    print header['whichblocks']
    print type(header['whichblocks'])
    saveBLK(header,data,fsave)
    
    