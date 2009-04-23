from pypsd.sectionbase import PSDParserBase
 
class PSDHeader(PSDParserBase):
    
    def __init__(self, fileObj):
        '''
        fileObj is opened file to be readed
        '''
        super(PSDHeader, self).__init__(fileObj)
            
        if not (hasattr(fileObj, "tell") and fileObj.tell() >= 0):  
            raise TypeError("First object should be file pointer.")
        
        self.signature = None
        self.version = None
        self.channels = None
        self.rows = None
        self.columns = None
        self.depth = None
        self.mode = None
                
    def __str__(self):
        return """Signature: %s
Version: %s
Channels: %s
Rows: %s
Columns: %s
Depth: %s
Mode: %s""" % (self.signature, self.version, self.channels, self.rows, 
               self.columns, self.depth, self.mode)

    def parse(self):
        if self.f.tell() != 0:
            raise BaseException("Pointer should be in the beginning.")
        
        self.signature = self.readString(4)
        if self.signature != self.SIGNATURE:
            raise BaseException("Signature must much should be %s but was %s" %  
                                (self.signature, self.SIGNATURE))
        
        self.version = self.readShortInt()
        #if self.signature != 1:
        # Always equal to 1. Do not try to read the file if the version does 
        #    raise BaseException("Signature must much should be %s but was %s" %  
        #                        (self.signature, self.SIGNATURE))
        
        self.skip(6)
        self.channels = self.readShortInt() #TODO 1-24 max
        self.rows = self.readInt() #TODO 1-30 000
        self.columns = self.readInt() #TODO 1-30 000
        self.depth = self.readShortInt() #TODO 1, 8, 16 .check for new versions
        self.mode = ColorSchema(self.readShortInt())

class ColorSchema(object):
    def __init__(self, code):
        self.code = code
        self.map = {0:"Bitmap", 1:"Grayscale", 2:"Indexed Color", 3:"RGB Color",
                    4:"CMYK Color", 7:"Multichannel", 8:"Duotone", 9:"Lab Color"}
        if self.code not in self.map:
            raise BaseException("Mode code should be from the list.")
        self.name = self.map[self.code]
        
    def __str__(self):
        return "%s (%d)" % (self.name, self.code)


class PSDColorMode(PSDParserBase):

    def __init__(self, fileObj):
        '''
        fileObj is opened file to be readed
        '''
        super(PSDColorMode, self).__init__(fileObj)
    
    def parse(self):
        self.updateLength(4)
        self.skip(self.length)


class PSDImageResources(PSDParserBase):
    
    def __init__(self, fileObj):
        '''
        fileObj is opened file to be readed
        '''
        super(PSDImageResources, self).__init__(fileObj)
    
    def parse(self):
        self.updateLength(4)
        self.skip(self.length) #TODO get Data


class PSDLayerMask(PSDParserBase):
    
    def __init__(self, fileObj):
        '''
        fileObj is opened file to be readed
        '''
        super(PSDImageResources, self).__init__(fileObj)
    
    def parse(self):
        self.updateLength(4)
        self.skip(self.length) #TODO get Data


class PSDImageData(PSDParserBase):
    
    def __init__(self, fileObj):
        '''
        fileObj is opened file to be readed
        '''
        self.compression = None
        super(PSDImageResources, self).__init__(fileObj)
    
    def parse(self):
        self.compression = ImageDataCompression(self.readShortInt())


class ImageDataCompression(object):
    def __init__(self, code):
        self.code = code
        self.map = {0:"Raw data", 1:"RLE compressed"}
        
        if self.code not in self.map:
            raise BaseException("Compression code should be from the list.")
        
        self.name = self.map[self.code]
        
    def __str__(self):
        return "%s (%d)" % (self.name, self.code)

