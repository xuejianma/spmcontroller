#-------------------------------------------------------------------------------
# Name:        PyParkTiff
# Purpose:     Import Park Tiff files as ParkTiff; Access scandata as a matrix;
#              Access specific scan settings; Save a matrix as a Park Tiff file.
#
# Author:      Xiaoyu Wu
#
# Created:     08/03/2015
# Copyright:   (c) Wu 2015
# Licence:     XYS-2015-002
# Acknowledgement: This module is written based on Yuan Ren's Igor program and Yongliang's Python program.
#-------------------------------------------------------------------------------

from PIL import Image
import struct as _struct
import numpy as _numpy
# import string
# import pyqtgraph as pg
import tkinter as Tkinter
from tkinter import filedialog as tkFileDialog
import struct
# from binascii import hexlify

#Infomation stored in ParkTiff Tags
METADATA_KEYS=['nImageType','s32SourceNameW','s08ImageModeW','dLPFStrength','nAutoFlatten','nFlattenOrder',\
              'nWidth','nHeight','dAngle','nSineScan','dOverScan','nFastScanDir',\
              'nSlowScanDir','nXYSwap','dXScanSize','dYScanSize','dXOffset','dYOffset',\
              'dScanRate','dSetPoint','s08SetPointUnitW','dTipBias','dSampleBias','dDataGain',\
              'dZScale','dZOffset','s08UnitW','nDataMin','nDataMax','nDataAvg',\
              'nCompression','nLogScale','nSquare','dZServoGain','dZScannerRange','s08XYVoltageMode',\
              's08ZVoltageMode','s08XYServoMode','nDataType','nXPDDRegion','nYPDDRegion','dAmplitude',\
              'dSelFrequency','dHeadTiltAngle','s16Cantilver']

#Positions to find the informations listed above
METADATA_POS=[0,4,68,84,92,96,\
              100,104,108,116,120,128,\
              132,136,140,148,156,164,\
              172,180,188,204,212,220,\
              228,236,244,260,264,268,\
              272,276,280,284,292,300,\
              316,332,348,352,356,360,\
              368,376,384,416]

def get_data_type_len(key):

        if key[0]=='n': # int
            return 'i', 4
        if key[0]=='d': # double
            return 'd', 8
        if key[0]=='s': # string
            return 's', int(key[1:3])*2


def get_field(key, metadatastring):
    if type(key) is type(0):
        idx=key
        key=METADATA_KEYS[key]

    typ, length = get_data_type_len(key)

    idx=METADATA_KEYS.index(key)
    pos=METADATA_POS[idx]

    if typ == 's':
        tempstr = str(metadatastring[pos:pos+length].decode('utf-16-le'))
        return tempstr.replace('\x00','')
    else:
        return _struct.unpack('<'+typ, metadatastring[pos:pos+length])[0]

#Function to open a ParkTiff file and return the scan data (not finished yet, old style, NOT RECOMMEND)
def OpenParkTiff():


    root = Tkinter.Tk()
    root.withdraw()
    file_path = tkFileDialog.askopenfilename()

    im=Image.open(file_path)
    metadatastring = im.tag.get(50435)
    scandata_0 = im.tag.get(50434)
    lines = get_field('nHeight', metadatastring)
    columns = get_field('nWidth', metadatastring)
    data_type = get_field('nDataType', metadatastring)
    print(lines, columns)

    scandata_1 = _numpy.array(scandata_0, dtype = 'uint8')
    scandata_2 = scandata_1.tostring()
    if (data_type == 0):
        scandata_3 = _numpy.fromstring(scandata_2, dtype='int16')
    elif (data_type == 2):
        scandata_3 = _numpy.fromstring(scandata_2, dtype='float32')
    print(scandata_3.shape)
    data=_numpy.reshape(scandata_3, [lines, columns])
    print(data.shape)


    ## Add path to library (just for examples; you do not need this)
    from pyqtgraph.Qt import QtCore, QtGui
    import pyqtgraph as pg
    pg.setConfigOption('background', 'w')

    app = QtGui.QApplication([])

    ## Create window with ImageView widget
    win = QtGui.QMainWindow()
    win.resize(800,800)
    imv = pg.ImageView()
    win.setCentralWidget(imv)
    win.show()
    win.setWindowTitle('pyqtgraph example: ImageView')


    ## Display the data
    imv.setImage(data)

    ## Start Qt event loop unless running in interactive mode.
    if __name__ == '__main__':
        import sys
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    return data

#Treat ParkTiff file as an object with scandata and metadata
class ParkTiff:



    def __init__(self, path = None):
        if (path == None):
            root = Tkinter.Tk()
            root.withdraw()
            self.file_path = tkFileDialog.askopenfilename()
        else:
            self.file_path = path

        im=Image.open(self.file_path)
        self.metadatastring = im.tag.get(50435)
        scandata_0 = im.tag.get(50434)
        lines = get_field('nHeight', self.metadatastring)
        columns = get_field('nWidth', self.metadatastring)
        data_type = get_field('nDataType', self.metadatastring)
        scandata_1 = _numpy.array(scandata_0, dtype = 'uint8')
        scandata_2 = scandata_1.tostring()
        if (data_type == 0):
            scandata_3 = _numpy.fromstring(scandata_2, dtype='int16')
        elif (data_type == 2):
            scandata_3 = _numpy.fromstring(scandata_2, dtype='float32')
        self.scandata = _numpy.reshape(scandata_3, [lines, columns])
        self.scandata = get_field('dDataGain', self.metadatastring)*(get_field('dZScale', self.metadatastring)*self.scandata+get_field('dZOffset', self.metadatastring))

    def show_tag(self, tag_name):
        print(tag_name,":", get_field(tag_name, self.metadatastring))

    def show_image(self):
        ## Add path to library (just for examples; you do not need this)
        from pyqtgraph.Qt import QtCore, QtGui
        import pyqtgraph as pg
        pg.setConfigOption('background', 'w')

        app = QtGui.QApplication([])

        ## Create window with ImageView widget
        win = QtGui.QMainWindow()
        win.resize(800,800)
        imv = pg.ImageView()
        win.setCentralWidget(imv)
        win.show()
        win.setWindowTitle('pyqtgraph example: ImageView')


        ## Display the data
        imv.setImage(self.scandata)

        ## Start Qt event loop unless running in interactive mode.
        if __name__ == '__main__':
            import sys
            if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
                QtGui.QApplication.instance().exec_()

def TiffAddTag(file_object, field_tag, field_type, field_num, field_value):
    file_object.write(struct.pack("<H", field_tag))
    file_object.write(struct.pack("<H", field_type))
    file_object.write(struct.pack("<i", field_num))
    file_object.write(struct.pack("<i", field_value))



def SaveParkTiff(data, X_scan_size, Y_scan_size, file_path):
    #data must be a numpy array

    tag_num = 9

    ImageWidth = data.shape[1]
    ImageHeight = data.shape[0]
    DataSize = ImageWidth * ImageHeight

    f = open(file_path, "wb")
    f.write(b"II")
    f.write(struct.pack("<H",42))
    f.write(struct.pack("<i",8))


    f.write(struct.pack("<H",tag_num))
    # ImageWidth
    TiffAddTag(f, 256, 3, 1, ImageWidth)
    # ImageHeight
    TiffAddTag(f, 257, 3, 1, ImageHeight)
    # BitPerSample
    TiffAddTag(f, 258, 3, 1, 8)
    # 8 byte header+2byte (num of tags)+N tags each uses 12 byte. Data will be written after Tags
    ThumbNailOffset=8+2+tag_num*12
    # StripOffsets
    TiffAddTag(f, 273, 4, 1, ThumbNailOffset)
    # RowsPerStrip
    TiffAddTag(f, 278, 3, 1, ImageHeight)
    # PSIA Magic Number
    TiffAddTag(f, 50432, 4, 1, 235082497)
    # PSIA version
    TiffAddTag(f, 50433, 4, 1, 16777218)
    # Image data will be written after thumbnail
    DataOffset=ThumbNailOffset+DataSize
    # PSIA data
    TiffAddTag(f, 50434, 1, 2*DataSize, DataOffset)
    # PSIA header, Header will be written after image data
    TiffAddTag(f, 50435, 1, 580, 2*DataSize+DataOffset)


    #Thumbnail
    DataMax = data.max()
    DataMin = data.min()
    for i in data:
        for j in i:
            val = (j-DataMin)/(DataMax-DataMin)*255
            f.write(struct.pack("<B", int(val)))

    #ScanData
    DataGain = max(abs(DataMax),abs(DataMin))/float(32767)
    for i in data:
        for j in i:
            val = j / DataGain
            f.write(struct.pack("<h", int(val)))

    f.write(struct.pack("x")*100)
    f.write(struct.pack("<I", ImageWidth))
    f.write(struct.pack("<I", ImageHeight))
    f.write(struct.pack("x")*32)

    # X scan size
    f.write(struct.pack("<d", X_scan_size))
    # Y scan size
    f.write(struct.pack("<d", Y_scan_size))
    f.write(struct.pack("x")*64)

    # DataGain
    f.write(struct.pack("<d", DataGain))
    # ZScale
    f.write(struct.pack("<d", 1))
    # ZOffset
    f.write(struct.pack("<q", 0))
    f.write(struct.pack("x")*16)

    # DataMin
    f.write(struct.pack("<i",int(DataMin/DataGain)))
    # DataMax
    f.write(struct.pack("<i",int(DataMax/DataGain)))
    f.write(struct.pack("x")*312)
    f.close()



def show_image(data):
    ## Add path to library (just for examples; you do not need this)
    from pyqtgraph.Qt import QtCore, QtGui
    import pyqtgraph as pg
    pg.setConfigOption('background', 'w')

    app = QtGui.QApplication([])

    ## Create window with ImageView widget
    win = QtGui.QMainWindow()
    win.resize(800,800)
    imv = pg.ImageView()
    win.setCentralWidget(imv)
    win.show()
    win.setWindowTitle('pyqtgraph example: ImageView')


    ## Display the data
    imv.setImage(data)

    ## Start Qt event loop unless running in interactive mode.
    if __name__ == '__main__':
        import sys
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()


#Example: import a Park Tiff file as object ParkTiff. Show specific tag, show image, and save the image as a Park Tiff
#image1 = ParkTiff(file_path)
#image1.show_tag("s08ImageModeW")
#image1.show_image()
#SaveParkTiff(image1.scandata, 256, 256, file_path_new)
# data = _numpy.loadtxt('conductivity.txt')
# SaveParkTiff(data, data.shape[1], data.shape[0], 'conductivity.tiff')
#data = _numpy.loadtxt('Ch2 retrace.txt')
#SaveParkTiff(data, data.shape[1], data.shape[0], 'Ch2 retrace.tiff')
