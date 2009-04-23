import unittest

def bytesToInt(bytes):
	shift = 0
	value = 0
	bb = reversed(bytes)
	for b in bb:
		value += (b << shift)
		shift += 8

	return value

class PSDParserBase(object):
	def __init__(self, fileObj):
		if fileObj is None:
			raise BaseException("File object should be specified.")
		self.f = fileObj
		self.SIGNATURE = "8BPS"
		self.length = None
		
		self.parse()
	
	def parse(self):
		raise NotImplementedError()
	
	def updateLength(self):
		self.length = self.readInt()
	
	def read(self, size):
		return self.f.read(size)
	
	def skip(self, size):
		self.read(size)
	
	def readCustomInt(self, size):
		value = bytesToInt(self.read(size))
		return value
	
	def readShortInt(self):
		return self.readCustomInt(2)
	
	def readInt(self):
		return self.readCustomInt(4)
	
	def readString(self, size):
		return str(self.read(size), "UTF-8")

class PSDBaseTest(unittest.TestCase):
	def testBytesToInt(self):
		value1 = bytesToInt(b'\x00\x01\x02\x03') 
		self.failUnlessEqual(0x10203, value1)
		value2 = bytesToInt(b'\xff\x14\x2a\x10') 
		self.failUnlessEqual(0xff142a10, value2)
		

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()