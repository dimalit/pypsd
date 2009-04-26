import unittest
import logging
import io
import os.path

module_logger = logging.getLogger("pypsd.sectionbase")

def bytesToInt(bytes):
	shift = 0
	value = 0
	bb = reversed(bytes)
	for b in bb:
		value += (b << shift)
		shift += 8

	module_logger.debug("bytesToInt method. In: %s, out: %s" % (bytes, value))
	return value

class PSDParserBase(object):
	def __init__(self, fileObj = None, *args, **kwargs):
		self.logger = logging.getLogger("pypsd.sectionbase.PSDParserBase")

		self.logger.debug(
				"__int__ method. In: fileObj=%s, args=%s, kwargs=%s" % \
				(fileObj, args, kwargs))

		super(PSDParserBase, self).__init__(*args, **kwargs)

		if fileObj is None or not isinstance(fileObj, io.BufferedReader):
			raise BaseException("File object should be specified.")
		self.f = fileObj
		self.SIGNATURE = "8BPS"
		self.SIGNATIRE_8BIM = "8BIM"
		self.length = None

		self.parse()

	def parse(self):
		raise NotImplementedError()

	def updateLength(self):
		self.length = self.readInt()
		self.logger.debug("updateLength method. read %d bytes" % self.length)

	def read(self, size):
		bytes = self.f.read(size)
		self.logger.debug("read method. In: size=%d. Out: bytes=%s" %
						(size, bytes))
		return bytes

	def skip(self, size):
		self.read(size)
		self.logger.debug("skip method. In: size=%d" % size)

	def readCustomInt(self, size):
		value = bytesToInt(self.read(size))
		self.logger.debug("readCustomInt method. In: size=%d. Out=%d" %
						(size, value))
		return value

	def readShortInt(self):
		ch1 = self.readCustomInt(1)
		ch2 = self.readCustomInt(1)
		if ch1 > 0:
			bytes =  -(256 - ch1)
		else:
			bytes = ch2
		self.logger.debug("readShortInt method. read bytes = %s" % bytes)
		return bytes

	def readInt(self):
		value = self.readCustomInt(4)
		self.logger.debug("readInt method. value = %d" % value)
		return value

	def readString(self, size):
		value = str(self.read(size), "UTF-8")
		self.logger.debug("readString method. In: size=%d. Out: %s" %
						(size, value))
		return value

	def getsize(self):
		return os.path.getsize(self.f.name)


class CodeMapObject(object):
	def __init__(self, code=None, map={}, *args, **kwargs):
		self.logger = logging.getLogger("pypsd.sectionbase.CodeMapObject")
		self.logger.debug(
				"__int__ method. In: code=%s, map=%s, args=%s, kwargs=%s" %
				(code, map, args, kwargs))
		super(CodeMapObject, self).__init__(*args, **kwargs)
		self.map = map
		self.code = code
		self.name = None
		self.updatename()

	def updatename(self):
		if self.code is not None:
			if self.code not in self.map:
				raise BaseException("Code should be from the list.")
			else:
				self.name = self.map[self.code]

		self.logger.debug("updatename method. In: code=%s, Out: name=%s" %
						(self.code, self.name))

	def __str__(self):
		return "%s (%s)" % (self.name, self.code)


class PSDBaseTest(unittest.TestCase):
	def testBytesToInt(self):
		value1 = bytesToInt(b'\x00\x01\x02\x03')
		self.failUnlessEqual(0x10203, value1)
		value2 = bytesToInt(b'\xff\x14\x2a\x10')
		self.failUnlessEqual(0xff142a10, value2)


if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()