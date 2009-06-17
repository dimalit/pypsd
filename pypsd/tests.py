import logging
import unittest

from pypsd.psdfile import PSDFile
from pypsd.sections import *

logging.config.fileConfig("./conf/logging.conf")

class PSDTest(unittest.TestCase):
	def setUp(self):
		self.testPSDFileName = "scroll.psd"

	def testPSDFile(self):
		psd = PSDFile(self.testPSDFileName)
		psd.parse()
		#psd.save()
		
#		layers = psd.layerMask.layers
#		self.assertEquals(20, len(layers))
#		
#		defaults = {"layerType":0, "opacity":255, "visibility":True, 
#				    "transpProtected":False, "clipping":False, "obsolete": False,
#				    "blendMode": {'code': 'norm', 'label': 'normal'},
#				    "pixelDataIrrelevant": False}
#		
#		checklist = [
#		{"name":"Background", "transpProtected":True},
#		{"name":"darken", "pixelDataIrrelevant":True, 
#		  "blendMode": {'code': 'dark', 'label': 'darken'}},  
#		{"name":"lockTrans", "transpProtected":True},
#		{"name":"invisible", "visibility":False},
#		{"name":"other", 
#		  "layerType":{'code': 1, 'label': 'open folder'},
#		  "pixelDataIrrelevant": True},
#		{"name":""},
#		{"name":""},
#		{"name":""}, ]
#		
#		for l in layers:
#			if l.layerType != 0:
#				pass
#			else:
#				
		
		#psd = PSDFile()
		#self.failUnlessRaises(BaseException, psd.parse)
		
		#self.failUnlessRaises(IOError, psd.parse)
		#psd = PSDFile(self.testPSDFileName)
		
		#print (psd)

#	def testPSDSections(self):
#		self.failUnlessRaises(BaseException, PSDHeader)
#		with open(self.testPSDFileName, mode = "rb") as f:
			#Header Parsing
#			header = PSDHeader(f)
#			self.failUnlessEqual(header.signature, "8BPS")
#			self.failUnlessEqual(header.version, 1)

			#trying to parse from begining, when we are not in begining
#			self.failUnlessRaises(BaseException, PSDHeader, f)

#			colorMode = PSDColorMode(f)
			#self.failUnlessEqual(colorMode.code, 0)
#			imageResources = PSDImageResources(f)
#			layerMask = PSDLayerMask(f)


if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()