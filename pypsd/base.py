import unittest
import logging
#Python 3.0: import io
import os.path
from ps_parser import PSParser 

module_logger = logging.getLogger("pypsd.sectionbase")

INFINITY = 'infinity'
ZERO = 0 
MINUS_ZERO = -0

def bytesToInt(bytes):
	shift = 0
	value = 0
	bb = reversed(bytes)
	for b in bb:
		b = ord(b) #line for Python 2.5
		value += (b << shift)
		shift += 8

	module_logger.debug("bytesToInt method. In: %s, out: %s" % (bytes, value))
	return value

def int2Binary(n):
	'''convert integer n to binary string bStr'''

	bStr = ''
	if n < 0: raise ValueError ("must be a positive integer")
	if n == 0: return '0'
	while n > 0:
		bStr = str(n % 2) + bStr
		n = n >> 1

	return bStr

def makeEven(n):
	if n & 0x01 != 0:
		n += 1
	return n

class PSDParserBase(object):
	
	def __init__(self, stream = None, psd = None):
		self.logger = logging.getLogger("pypsd.base.PSDParserBase")

		self.debugMethodInOut("__init__")

		if stream is None: #or not isinstance(stream, io.BufferedReader):
			raise BaseException("File object should be specified.")
		
		self.stream = stream
		self.psd = psd
		
		'''
		Constants.
		'''
		self.SIGNATURE = "8BPS"
		self.SIGNATIRE_8BIM = "8BIM"
		self.VERSION = 1
		self.CHANNELS_RANGE = [1, 56]
		self.SIZE_RANGE = [1, 30000]
		self.DEPTH_LIST = [1,8,16]
		self.OPACITY_RANGE = [0, 255]
		
		'''
		Start parse Method of the child.
		'''

		self.parse()

	def parse(self):
		pass
	
	def skip(self, size):
		self.stream.seek(size, 1) #whence=
		self.debugMethodInOut("skip", {"size":size})
	
	def readUnicodeString(self):
		charsNumber = self.readInt()
		unicode_string = u''
		for i in range(charsNumber):
			char_code = self.readShortInt()
			if char_code > 0:
				unicode_string += unichr(char_code)
		return unicode_string
	
	def skipIntSize(self):
		size = self.readInt()
		self.skip(size)
		self.debugMethodInOut("skipIntSize",result="skipped=%s" % size)	
	
	def readCustomInt(self, size, negative=False):
		#Python 3: value = bytesToInt(self.stream.read(size))
		#Python 2.6: bb = bytearray(size)
		#Python 2.6: self.stream.readinto(bb)
		bb = self.stream.read(size)
		value = bytesToInt(bb)
		
		if negative:
			if value > pow(2, (size * 8) - 1):
				value = int(-(pow(2, size * 8) - value))
		
		self.debugMethodInOut("readCustomInt", {"size":size}, result=value)
		return value

	def readDouble(self):
		b1 = self.readInt(4)
		b2 = self.readInt(4)
		long = b1 << 32 | b2
		signbit = long >> 63
		expan = long >> 52 & 0xfff >> 1
		if expan >= 0x7ff:
			return INFINITY
		elif expan == 0x000:
			return ZERO
		elif expan == 0x800:
			return MINUS_ZERO
		signif = ((long & 0xfffffffffffff) | (1<<52)) * pow(2, -52)
		
		return pow(-1, signbit) * pow(2, expan-1023) * signif
		
		
	def readInt(self, returnEven=False, isLong=True):
		value = self.readCustomInt(4, negative=not isLong)
		
		if returnEven:
			value = makeEven(value)
		
		self.debugMethodInOut("readInt", result=value)
		return value

	def readShortInt(self):
		value = self.readCustomInt(2, negative=True)
		self.debugMethodInOut("readShortInt", result=value)
		return value
	
	def readTinyInt(self):
		tinyInt = self.readCustomInt(1)
		
		self.debugMethodInOut("readTinyInt", result=tinyInt)
		return tinyInt
	
	def readBytesList(self, size):
		#Python 2.6: barray = bytearray(size)
		#Python 2.6: bytesRead = self.stream.readinto(barray)
		bytesRead = self.stream.read(size)
		self.logger.debug("Bytes read: %s" % bytesRead)
		result = [ord(b) for b in bytesRead]
		
		self.debugMethodInOut("readBits", {"size":size}, result)
		return result
	
	def readBits(self, size):
		i = self.readCustomInt(size)
		#Python 2.6: bits = [int(b) for b in bin(i)[2:]]
		bits = [int(b) for b in int2Binary(i)]
		bits.reverse()
		moreZeros = size * 8 - len(bits)
		bits = bits + [0] * moreZeros
		
		self.debugMethodInOut("readBits", {"size":size}, bits)
		return bits

	def readPascalString(self):
		size = self.readTinyInt()
		if size == 0:
			self.skip(1)
			return ""
		else: 
			size = size & 0xFF
			size = ((size + 1 + 3) & ~0x03) - 1
			name = self.readString(size)
		
		return name
		
	def readString(self, size):
		dataRead = self.stream.read(size)
		#Python 3:value = str(dataRead, "UTF-8")
		value = str(dataRead)
		value = "".join([s for s in value if ord(s) != 0]) #0 is padding char
		self.debugMethodInOut("readString", {"size":size}, value)
		
		return value

	def getSize(self):
		return os.path.getsize(self.stream.name)
	
	def getRectangle(self):
		top = self.readInt(isLong=False)
		left = self.readInt(isLong=False)
		bottom = self.readInt(isLong=False)
		right  = self.readInt(isLong=False)
		width  = right-left
		height = bottom-top
		
		return {"top":top, "left":left, "bottom":bottom, "right":right, 
			    "width":width, "height":height}
	
	def getPos(self):
		return self.stream.tell()
	
	def skipRest(self, blockStart, blockSize):
		toSkip = blockStart + blockSize - self.getPos()
		self.skip(toSkip)
	
	def getCodeLabelPair(self, code, map):
		return {"code":code, "label":map[code]}
	
	def debugMethodInOut(self, label, invars={}, result=None):
		message = "%s method." % label
		
		if invars:
			invars = ["%s=%s" % (name, invars[name]) for name in invars]
			message += "In: %s" % ", ".join(invars)
			
		if result:
			message += " Out: %s" % result
			
		self.logger.debug(message)
	
	def readOsType(self):
		descriptor = {}
		value = None
		osType = self.readString(4)
		if osType == "TEXT": #String
			value = self.readUnicodeString()
		elif osType == "enum": #Enumerated
			typeID = self.readLengthWithString()
			enum = self.readLengthWithString()
			value = {"typeID": typeID, "enum": enum}
		elif osType in ['Objc', 'GlbO']:  #Descriptor, GlobalObject same as Descriptor
			typeID = self.readLengthWithString()
			enum = self.readLengthWithString()
			value = {"typeID": typeID, "enum": enum}
		elif osType == 'VlLs':  #List
			list_size = self.readInt()
			value = []
			for k in range(list_size):
				value.append(self.readOsType())
		elif osType == 'doub':  #Double
			value = self.readDouble()
		elif osType == 'UntF':  #Unit float
			unitType = self.readString(4)
			#TODO Validate
			unitValue = self.readDouble()
			value = {'type':unitType, 'value':unitValue}
		elif osType == 'long':  #Integer
			value = self.readInt()
		elif osType == 'bool':  #Boolean
			value = self.readBoolean()
		elif osType in ['type', 'GlbC']:  #GlbC'= Class
			name = self.readUnicodeString()
			classID = self.readLengthWithString()
			value = {'name':name, 'classID':classID}
		elif osType == 'alis':  #Alias
			data_length = self.readInt()
			value = self.readString(data_length)
		elif osType == 'obj ':   #Reference
			obj_items_num = self.readInt()
			for j in range(obj_items_num):
				ref_obj_type = self.readString(4)
				if ref_obj_type == 'prop': #Property
					name = self.readUnicodeString()
					classID = self.readLengthWithString()
					keyID = self.readLengthWithString()
				elif ref_obj_type == 'Clss': #Class
					name = self.readUnicodeString()
					classID = self.readLengthWithString()
				elif ref_obj_type == 'Enmr': #Enumerated Reference
					name = self.readUnicodeString()
					classID = self.readLengthWithString()
					typeID = self.readLengthWithString()
					enum = self.readLengthWithString()
				elif ref_obj_type == 'rele': #Offset
					name = self.readUnicodeString()
					classID = self.readLengthWithString()
					offsetValue = self.readInt()
				elif ref_obj_type == 'Idnt': #Identifier
					pass
				elif ref_obj_type == 'indx': #Index
					pass
				elif ref_obj_type == 'name': #Name
					pass
		elif osType == 'tdta': #Some strange types.
			data_length = self.readInt()
			pos = self.getPos()
			data_string = self.readString(data_length)
			p = PSParser(source=data_string)
			value = p.parse()
			self.skipRest(pos, data_length)

		return {'type': osType, 'value': value}
		
	
	def readDescriptorStructure(self):
		name_from_classID = self.readUnicodeString()
		classID = self.readLengthWithString()
		items_num = self.readInt()
		descriptors = {}
		for i in range(items_num):
			txt_key = self.readLengthWithString().strip()
			descriptors[txt_key] = self.readOsType()
		return descriptors
	
	def readBoolean(self):
		byte = self.readTinyInt()
		return byte != 0
	
	def readLengthWithString(self, default_length=4):
		length = self.readInt()
		if length == 0:
			value = self.readString(default_length)
		else:
			value = self.readString(length)
			
		return value
#class CodeMapObject(object):
#	def __init__(self, code=None, map={}, *args, **kwargs):
#		self.logger = logging.getLogger("pypsd.base.CodeMapObject")
#		self.logger.debug(
#				"__int__ method. In: code=%s, map=%s, args=%s, kwargs=%s" %
#				(code, map, args, kwargs))
#		super(CodeMapObject, self).__init__(*args, **kwargs)
#		self.map = map
#		self.code = code
#		self.name = None
#		self.updatename()
#
#	def updatename(self):
#		if self.code is not None:
#			if self.code not in self.map:
#				raise BaseException("Code should be from the list.")
#			else:
#				self.name = self.map[self.code]
#
#		self.logger.debug("updatename method. In: code=%s, Out: name=%s" %
#						(self.code, self.name))
#
#	def __str__(self):
#		return "%s (%s)" % (self.name, self.code)


class PSDBaseTest(unittest.TestCase):
	def testBytesToInt(self):
		#Python 2.6: b''
		value1 = bytesToInt('\x00\x01\x02\x03')
		self.failUnlessEqual(0x10203, value1)
		value2 = bytesToInt('\xff\x14\x2a\x10')
		self.failUnlessEqual(0xff142a10, value2)
	
	def testReadCustomInt(self):
		from base import PSDParserBase
		from StringIO import StringIO
		
		stream = StringIO()
		stream.write('\xff\xff\xff\xfe')
		stream.write('\xff\xff\xff\xff')
		stream.write('\xf0\x00\x00\x00')
		stream.write('\xff\xff\xff\xfe')
		stream.write('\x0f\xff')
		
		stream.write('\xc0\x00\x00\x00\x00\x00\x00\x00')
		stream.write('\x40\x00\x00\x00\x00\x00\x00\x00')
		stream.write('\x3f\xf0\x00\x00\x00\x00\x00\x02')
		
		stream.write('\x7f\xf0\x00\x00\x00\x00\x00\x00')
		stream.write('\x00\x00\x00\x00\x00\x00\x00\x00')
		stream.write('\x80\x00\x00\x00\x00\x00\x00\x00')
		
		stream.seek(0)
		
		p = PSDParserBase(stream)
		assert p.readCustomInt(4) == 0xFFFFFFFE
		assert p.readCustomInt(4, negative=True) == -1
		assert p.readCustomInt(4, negative=True) == -0x0fffffff-1
		assert p.readCustomInt(4, negative=True) == -2
		assert p.readCustomInt(2, negative=True) == 0xfff
		d1 = p.readDouble()
		d2 = p.readDouble()
		d3 = p.readDouble()
		infinity = p.readDouble()
		zero = p.readDouble()
		minuszero = p.readDouble()
		assert d1 == -2
		assert d2 == 2
		assert d3 == 1.0000000000000004
		assert d3 != 1.0000000000000006
		assert infinity == INFINITY
		assert zero == ZERO
		assert minuszero == MINUS_ZERO
		

if __name__ == "__main__":
	#import sys;sys.argv = ['', 'Test.testName']
	unittest.main()