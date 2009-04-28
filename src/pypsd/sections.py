import logging
from pypsd.sectionbase import PSDParserBase,CodeMapObject

class PSDHeader(PSDParserBase):
	'''
	The file header is fixed length, the other four sections are variable
	in length.

	When writing one of these sections, you should write all fields in
	the section, as Photoshop may try to read the entire section.
	Whenever writing a file and skipping bytes, you should explicitly write
	zeros for the skipped fields.

	When reading one of the length delimited sections, use the
	length field to decide when you should stop reading. In most cases,
	the length field indicates the number of bytes, not records following.

	File header section
	The file header contains the basic properties of the image.

	Table 10-4: File header
	Length 		Name
	4 bytes 	Signature
	2 bytes 	Version
	6 bytes 	Reserved
	2 bytes 	Channels
	4 bytes 	Rows
	4 bytes 	Columns
	2 bytes		Depth
	2 bytes 	Mode
	'''

	def __init__(self, fileObj):
		'''
		fileObj is opened file to be readed
		'''
		self.logger = logging.getLogger("pypsd.sections.PSDHeader")
		self.logger.debug("__init__ method. In: fileObj=%s" % fileObj)

		if hasattr(fileObj, "tell") and fileObj.tell() != 0:
			raise TypeError("Argument should be file pointer and it should be "
							"at the beginning of file")

		self.signature = None
		self.version = None
		self.channels = None
		self.rows = None
		self.columns = None
		self.depth = None
		self.mode = None

		super(PSDHeader, self).__init__(fileObj)





	def parse(self):
		self.logger.debug("parse method.")

		'''
		Signature. 4 bytes.
		Always equal to '8BPS'.
		Do not try to read the file if the signature does not match this value.
		'''
		self.signature = self.readString(4)
		self.logger.debug("Signature: %s" % self.signature)

		if self.signature != self.SIGNATURE:
			raise BaseException("Signature must much should be %s but was %s" %
								(self.signature, self.SIGNATURE))

		'''
		Version. 2 bytes.
		Always equal to 1. Do not try to read the file if the version does
		not match this value.
		'''
		self.version = self.readShortInt()
		self.logger.debug("Version: %d" % self.version)
		#if self.signature != 1:
		# Always equal to 1. Do not try to read the file if the version does
		#    raise BaseException("Signature must much should be %s but was %s" %
		#                        (self.signature, self.SIGNATURE))

		'''6 bytes 	Reserved 	Must be zero.'''
		self.skip(6)

		'''
		Channels. 2 bytes.
		The number of channels in the image, including any alpha channels.
		Supported range is 1 to 24.
		'''
		self.channels = self.readShortInt() #TODO 1-24 max
		self.logger.debug("Channels: %d" % self.channels)

		'''
		Rows. 4 bytes.
		The height of the image in pixels. Supported range is 1 to 30,000.
		'''
		self.rows = self.readInt() #TODO 1-30 000
		self.logger.debug("Rows (Height): %d" % self.rows)

		'''
		Columns. 4 bytes.
		The width of the image in pixels. Supported range is 1 to 30,000.
		'''
		self.columns = self.readInt() #TODO 1-30 000
		self.logger.debug("Columns (Width): %d" % self.columns)

		'''
		Depth. 2 bytes.
		The number of bits per channel. Supported values are 1, 8, and 16.
		'''
		self.depth = self.readShortInt() #TODO 1, 8, 16 .check for new versions
		self.logger.debug("Color Depth: %d" % self.depth)

		'''
		Mode. 2 bytes.

		'''
		self.mode = ColorSchema(self.readShortInt())
		self.logger.debug("Color Schema: %s" % self.mode)

	def __str__(self):
		return  ("==Header==\nSignature: %s\n"
				"Version: %s\n"
				"Channels: %s\n"
				"Rows: %s\n"
				"Columns: %s\n"
				"Depth: %s\n"
				"Mode: %s" % (self.signature, self.version, self.channels, self.rows,
							self.columns, self.depth, self.mode))

class ColorSchema(CodeMapObject):
	'''
	The color mode of the file. Supported values are:
	Bitmap = 0
	Grayscale = 1
	Indexed Color = 2
	RGB Color = 3
	CMYK Color = 4
	Multichannel = 7
	Duotone = 8
	Lab Color = 9
	'''

	def __init__(self, code=None, *args, **kwargs):
		self.logger = logging.getLogger("pypsd.sections.ColorSchema")
		self.logger.debug("__init__ method. In: code=%s, args=%s, kwargs=%s" %
						(code, args, kwargs))

		super(ColorSchema, self).__init__(code=code, map=
				{0:"Bitmap", 1:"Grayscale", 2:"Indexed Color", 3:"RGB Color",
				4:"CMYK Color", 7:"Multichannel", 8:"Duotone", 9:"Lab Color"})



class PSDColorMode(PSDParserBase, CodeMapObject):
	'''
	Only indexed color and duotone have color mode data. For all other
	modes, this section is just 4 bytes: the length field, which is set to zero.

	For indexed color images, the length will be equal to 768, and the
	color data will contain the color table for the image, in non-interleaved
	order.

	For duotone images, the color data will contain the duotone specification,
	the format of which is not documented. Other applications that read
	Photoshop files can treat a duotone image as a grayscale image,
	and just preserve the contents of the duotone information when reading
	and writing the file.
	'''

	def __init__(self, fileObj=None, *args, **kwargs):
		'''
		fileObj is opened file to be readed
		'''
		self.logger = logging.getLogger("pypsd.sections.PSDColorMode")
		self.logger.debug("__init__ method. In: fileObj=%s, args=%s, kwargs=%s" %
						(fileObj, args, kwargs))

		super(PSDColorMode, self).__init__(fileObj=fileObj,
										map={0:"Other", 768:"Indexed Colors" })

	def parse(self):
		'''
		Length. 4 bytes.
		The length of the following color data.
		'''
		self.updateLength()
		self.skip(self.length)
		self.code = self.length
		super(PSDColorMode, self).updatename()

		'''
		Color data. Variable.
		The color data.
		'''
		self.data = None #TODO Process color data

		self.logger.debug("parse method. Length: %s, Mode Name: %s" %
						(self.length, self.name))

	def __str__(self):
		return "==Color Mode==\n%s" % super(PSDColorMode, self).__str__()


class PSDImageResources(PSDParserBase):
	'''
	The third section of the file contains image resources. As with
	the color mode data, the section is indicated by a length field
	followed by the data.
	'''

	def __init__(self, fileObj):
		'''
		fileObj is opened file to be readed
		'''
		self.logger = logging.getLogger("pypsd.sections.PSDImageResources")
		self.logger.debug("__init__ method. In: fileObj=%s" % fileObj)

		super(PSDImageResources, self).__init__(fileObj)
		#TODO Make it!

	def parse(self):
		self.logger.debug("parse method.")
		self.updateLength()

		self.skip(self.length) #TODO real Data

	def __str__(self):
		return "==Image Resources==\nLength:%d" % self.length;


class PSDLayerMask(PSDParserBase):
	'''
	The fourth section contains information about Photoshop 3.0 layers
	and masks.
	If there are no layers or masks, this section is just 4 bytes:
	the length field, which is set to zero.

	Table 10-7: Layer and mask information
	Length 		Name 		Description

	4 bytes 	Length 		Length of the miscellaneous information section.

	Variable 	Layers 		Layer info. See table 10-10.
	Variable 	Masks 		One or more layer mask info structures.
							See table 10-13.

	Table 10-10. Layer structure
	Length 		Name 		Description

	2 bytes 	Count 		Number of layers.
					If <0, then number of layers is absolute value,
					and the first alpha channel contains the transparency
					data for the merged result.
	Variable 	Layer 		Information about each layer (table 10-11).


	Table 10-12: Channel length info
	Length 		Name 		Description

	2 bytes 	Channel ID 	0 = red, 1 = green, etc.
					-1 = transparency mask
					-2 = user supplied layer mask
	4 bytes 	Length 		Length of following channel data.


	Table 10-13: Layer mask data
	Length 		Name 		Description

	4 bytes 	Size 		Size of layer mask data. This will be
					either 0x14, or zero (in which case the
					following fields are not present).
	4 bytes 	Top 		Rectangle enclosing layer mask.
	4 bytes 	Left
	4 bytes 	Bottom
	4 bytes 	Right
	1 byte 		Default color 	0 or 255
	1 byte 		Flags 		bit 0: position relative to layer
					bit 1: layer mask disabled
					bit 2: invert layer mask when blending
	2 bytes 	Padding 	Zeros
	'''

	def __init__(self, fileObj):
		'''
		fileObj is opened file to be readed
		'''
		self.logger = logging.getLogger("pypsd.sections.PSDLayerMask")
		self.logger.debug("__init__ method. In: fileObj=%s" % fileObj)

		self.layersCount = None
		self.masklength = None
		self.layers = []

		super(PSDLayerMask, self).__init__(fileObj)

	def parse(self):
		self.logger.debug("parse method")
		self.updateLength()
		#self.skip(self.layerslength) #TODO get Data

		self.layerInfoLength = self.readInt()

		self.layersCount = self.readShortInt()
		for i in range(self.layersCount):
			#process each layer
			#layers.append()
			layer = PSDLayer(self.f)
			self.layers.append(layer)

		self.masklength = self.readInt()
		self.skip(self.masklength) #TODO get Data

	def __str__(self):
		return ("==Layer Mask==\n"
				"Whole Length: %d\n"
				"Layers count: %d\n"
				"Mask Length: %d" %
				(self.length, self.layersCount, self.masklength));

class PSDLayer(PSDParserBase):
	'''

	1 byte 		(filler) 	(zero)
	4 bytes 	Extra data size Length of the extra data field. This is
					the total length of the next five fields.
	24 bytes, or 4 bytes if no layer mask.
			Layer mask data	See table 10-13.
	Variable 	Layer blending ranges i
					See table 10-14.
	Variable 	Layer name 	Pascal string, padded to a multiple of 4 bytes.
	'''
	def __init__(self, fileObj):
		'''
		fileObj is opened file to be readed
		'''
		self.logger = logging.getLogger("pypsd.sections.PSDLayer")
		self.logger.debug("__init__ method. In: fileObj=%s" % fileObj)

		self.top = None
		self.left = None
		self.bottom = None
		self.right = None
		self.channels = {}
		self.blend = ()
		self.opacity = None
		self.clipping = ()


		super(PSDLayer, self).__init__(fileObj)

	def parse(self):
		#The rectangle containing the contents of the layer.
		self.top = self.readInt()    #4 bytes 	Layer top
		self.left = self.readInt()   #4 bytes 	Layer left
		self.bottom = self.readInt() #4 bytes 	Layer bottom
		self.right = self.readInt()  #4 bytes 	Layer right

		#2 bytes 	Number channels The number of channels in the layer.
		self.chanelsCount = self.readShortInt()

		#Variable 	Channel information. This contains a six byte record
		#for each channel. See table 10-12.
		for i in range(self.chanelsCount):
			channelId = self.readShortInt()
			channelLength = self.readInt()
			if channelId in self.channels:
				if type(self.channels[channelId]) == list:
					self.channels[channelId].append(channelLength)
				else:
					self.channels[channelId] = [self.channels[channelId]]
			else:
				self.channels[channelId] = channelLength

		#4 bytes 	Blend mode signature. Always '8BIM'.
		bimSignature = self.readString(4)
		assert bimSignature == self.SIGNATIRE_8BIM

		#4 bytes 	Blend mode key
		blendMap = {"norm":"normal",  "dark":"darken", "lite":"lighten",
					"hue":"hue", "sat":"saturation", "colr":"color",
					"lum":"luminosity", "mul":"multiply", "scrn":"screen",
					"diss":"dissolve", "over":"overlay", "hLit":"hard light",
					"sLit":"soft light", "diff":"difference"}
		blendCode = self.readString(4)
		self.blend = (blendCode, blendMap[blendCode])

		#1 byte 		Opacity 	0 = transparent ... 255 = opaque
		self.opacity = self.readTinyInt()

		#1 byte 		Clipping 	0 = base, 1 = non-base
		clippingMap = {0:"base", 1:"non-base"}
		clippingCode = self.readTinyInt()
		self.clipping = (clippingCode, clippingMap[clippingCode])

		#1 byte 		Flags 		bit0: transparency protected, bit1: visible
		flagsBits = self.readBits(1)
		self.transpProtected = flagsBits[0]
		self.visible =  flagsBits[1]

class PSDImageData(PSDParserBase):
	'''
	The image pixel data is the last section of a Photoshop
	3.0 file. Image data is stored in planar order, first all the red
	data, then all the green data, etc. Each plane is stored in
	scanline order, with no pad bytes.

	If the compression code is 0, the image data is just the raw image data.

	If the compression code is 1, the image data starts with the byte counts
	for all the scan lines (rows * channels), with each count stored
	as a two-byte value. The RLE compressed data follows, with each
	scan line compressed separately. The RLE compression is the same
	compression algorithm used by the Macintosh ROM routine PackBits,
	and the TIFF standard.

	Table 10-8: Image data
	Length 		Name 		Description

	2 bytes 	Compression 	Compression method. Raw data = 0, RLE compressed = 1.
	Variable 	Data 		The image data.
	'''

	def __init__(self, fileObj):
		'''
		fileObj is opened file to be readed
		'''
		self.logger = logging.getLogger("pypsd.sections.PSDImageData")
		self.logger.debug("__init__ method. In: fileObj=%s" % fileObj)
		self.compression = None
		self.bytesleft = None
		super(PSDImageData, self).__init__(fileObj)

	def parse(self):
		self.compression = ImageDataCompression(self.readShortInt())
		self.bytesleft = self.getsize() - self.f.tell()
		self.logger.debug("parse method. Compression=%s" % self.compression)


	def __str__(self):
		return ("==Image Data==\nCompression: %s\n"
			"Bytes Left: %d" % (self.compression, self.bytesleft));

class ImageDataCompression(CodeMapObject):
	def __init__(self, code):
		self.logger = logging.getLogger("pypsd.sections.ImageDataCompression")
		super(ImageDataCompression, self).__init__(code,
											{0:"Raw data", 1:"RLE compressed"})
		self.logger.debug("__init__ method. In: code=%s, name=%s" %
						(self.code, self.name ))

