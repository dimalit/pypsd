import os

from pypsd.sections import PSDHeader, PSDColorMode


class PSDFile(object):
    '''
    Main class. Contains all information about PSD file.
    '''

    def __init__(self, fileName = None):
        self.header = None
        self.colorMode = None
        self.imageResources = None
        self.layerMask = None
        self.imageData = None
        
        self.fileName = fileName;
    
    def parse(self):
        '''
        Parse PDF file and fill all self field.
        '''
        if self.fileName is None:
            raise BaseException("File Name not specified.")
        
        if not os.path.exists(self.fileName):
            raise IOError("Can't find file specified.")
        
        with open(self.fileName, mode = 'rb') as f:
            self.header = PSDHeader(f)
            self.colorMode = PSDColorMode(f)
            #self.... = PSD...(f)
            #self.... = PSD...(f)
            