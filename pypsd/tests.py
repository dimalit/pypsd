import logging
import unittest
from psdfile import PSDFile
from sections import *

logging.config.fileConfig("%s/conf/logging.conf" % os.path.dirname(__file__))

class PSDTest(unittest.TestCase):
	def setUp(self):
		self.testPSDFileName = "./../samples/5x5.psd"

	def testPSDFile(self):
		psd = PSDFile()
		self.failUnlessRaises(BaseException, psd.parse)

		psd = PSDFile(self.testPSDFileName)
		psd.parse()
		psd.save(dest="../samples/")
		
		layers = psd.layerMask.layers
		self.assertEquals(20, len(layers))
		
		defaults = {"layerType":0, 
				    "opacity":255, 
				    "visible":True, 
				    "transpProtected":False, 
				    "clipping":False, 
				    "obsolete": False,
				    "blendMode": {'code': 'norm', 'label': 'normal'},
				    "pixelDataIrrelevant": False}
		
		checklist = [
			{"name":"Background", "transpProtected":True},
			{"name":"darken", "pixelDataIrrelevant":False, 
		    "blendMode": {'code': 'dark', 'label': 'darken'}},  
			{"name":"lockTrans", "transpProtected":True},
			{"name":"invisible", "visible":False},
			{"name":"other", 
			  "layerType":{'code': 1, 'label': 'open folder'},
			  "pixelDataIrrelevant": True},
			{"name":""}, ]
		#parent_folder => [children_layers]
		hierarchy = {"colors": ["blue","colors"],
					 "Insider": ["cross"],
					 "Invisible":["layer"],
					 "closed":["layer2"],
					 "other":["invisible", "lockTrans", "darken"]}
		
		#TODO!!!
		for l in layers:
			if l.layerType != 0:
				pass
			else:
				for parent, layersList in hierarchy.items():
					for la in layersList:
						if l.name == la:
							print "Layer: %s have parent: %s" % (l.name, l.parent.name)
							self.assertEquals(parent, l.parent.name)
						
				for dd in checklist:
					if l.name == dd["name"]:
						for k,v in dd.items():
							print "Attr: %s => %s ? %s" % (k, v, getattr(l, k))
							self.assertEquals(v, getattr(l, k))
							
		


if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()