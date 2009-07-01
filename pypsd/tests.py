import logging
import unittest
import tempfile
import os.path
from psdfile import PSDFile, make_valid_filename
from sections import *

logging.config.fileConfig("%s/conf/logging.conf" % os.path.dirname(__file__))

class PSDTest(unittest.TestCase):
	def setUp(self):
		self.testPSDFileName2 = "./../samples/5x5.psd" 
		
	
	def test_make_valid_filename(self):
		path = "%s/test/\*?:file.tmp" % tempfile.gettempdir()
		real_path = "%s/testfile.tmp" % tempfile.gettempdir()
		if not os.path.exists(real_path):
			w = open(real_path, "w")
			w.close()
		layer_name = "test/\*?:file"
		right_layer_name = "testfile"
		layer_id = 15
		test_layer_name = make_valid_filename(path, layer_name, layer_id)
		self.assertEquals("%s%d" %(right_layer_name, layer_id), test_layer_name)

		path = "%s/test/\*?:folder" % tempfile.gettempdir()
		real_path = "%s/testfolder" % tempfile.gettempdir()
		if not os.path.exists(real_path):
			os.mkdir(real_path)
		layer_name = "test/\*?:folder"
		right_layer_name = "testfolder"
		layer_id = 15
		test_layer_name = make_valid_filename(path, layer_name, layer_id)
		self.assertEquals("%s%d" %(right_layer_name, layer_id), test_layer_name)
	
	def testPSDFile(self):
		testPSDFilesDir = "./../samples/"
		for entry in os.listdir(testPSDFilesDir):
			ispsd = os.path.splitext(entry)[1].lower()
			filepath = os.path.join(testPSDFilesDir, entry)
			if os.path.isfile(filepath) and ispsd == ".psd":
				psd = PSDFile(filepath)
				psd.parse()
				psd.save(dest="../samples/")
				os.chdir("..")
		
		
		testPSDFileName = "./../samples/5x5.psd"
		psd = PSDFile()
		self.failUnlessRaises(BaseException, psd.parse)

		psd = PSDFile(testPSDFileName)
		psd.parse()
		psd.save(dest="../samples/")

		layers = psd.layerMask.layers
		self.assertEquals(25, len(layers))

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