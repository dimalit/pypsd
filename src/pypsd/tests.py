from psdfile import PSDFile 
from pypsd.sections import PSDHeader
import unittest

class PSDTest(unittest.TestCase):
    def setUp(self):
        self.testPSDFileName = "scroll.psd"
        
    def testPSDFile(self):
        psd = PSDFile()
        self.failUnlessRaises(BaseException, psd.parse)
        psd = PSDFile("fakefilename")
        self.failUnlessRaises(IOError, psd.parse)
        psd = PSDFile(self.testPSDFileName)
        psd.parse()
    
    def testPSDHeader(self):
        self.failUnlessRaises(BaseException, PSDHeader)
        with open(self.testPSDFileName, mode = "rb") as f:
            header = PSDHeader(f)
            self.failUnlessEqual(header.signature, "8BPS")
            self.failUnlessEqual(header.version, 1)
            
            #trying to parse from begining, when we are not in begining
            self.failUnlessRaises(BaseException, PSDHeader, f)
            print (header)
        
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()