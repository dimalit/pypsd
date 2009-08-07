from __future__ import division
import logging
from base import PSDParserBase
#Python 3: import io
import StringIO
from PIL import Image

def validate(label, value, range=None, mustBe=None, list=None):
	assert label is not None
	assert value is not None or range is not None or list is not None
	if mustBe:
		if value != mustBe:
			raise BaseException("%s should be %s but was %s" % 
							    (label, mustBe, value))
	elif range:
		if value < range[0] or value > range[-1]:
			raise BaseException(
				"%s must be between %d and %d, but was %s" %
				(label, range[0], range[-1], value))
	elif list:
		if value not in list:
			raise BaseException(
				"%s must be one of %s, but was %s" %
				(label, list, value))
	

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
	'''

	def __init__(self, stream, psd):
		self.logger = logging.getLogger("pypsd.sections.PSDHeader")
		self.debugMethodInOut("__init__")
		
		#Python 3: or not isinstance(stream, io.BufferedReader) and \
		if stream is None and stream.tell() != 0:
			raise TypeError("Argument should be file pointer and it should be "
							"at the beginning of file")

		self.signature = None
		self.version = None
		self.channelsNum = None
		self.rows = None
		self.width = None
		self.height = None
		self.depth = None
		self.colorMode = None

		super(PSDHeader, self).__init__(stream, psd)

	def parse(self):
		self.debugMethodInOut("parse")

		'''
		4 bytes.
		Signature: Always equal to '8BPS'.
		Do not try to read the file if the signature does not match this value.
		'''
		self.signature = self.readString(4)
		self.logger.debug("Signature: %s" % self.signature)
		validate("Signature", self.signature, mustBe=self.SIGNATURE)

		'''
		2 bytes.
		Version: Always equal to 1. Do not try to read the file if the version 
		does not match this value.
		'''
		self.version = self.readShortInt()
		self.logger.debug("Version: %d" % self.version)
		validate("Version", self.version, mustBe=self.VERSION)

		'''
		6 bytes.
		Reserved: Must be zero.'''
		self.skip(6)

		'''
		2 bytes.
		Channels: The number of channels in the image, including any alpha channels.
		Supported range is 1 to 56.
		'''
		self.channelsNum = self.readShortInt()
		self.logger.debug("Channels #: %d" % self.channelsNum)
		validate("Channels number", self.channelsNum, range=self.CHANNELS_RANGE)

		'''
		4 bytes.
		Height: The height of the image in pixels. Supported range is 1 to 30,000.
		'''
		self.height = self.readInt()
		self.logger.debug("Height: %d" % self.height)
		validate("Height", self.height, range=self.SIZE_RANGE)

		'''
		4 bytes.
		Width: The width of the image in pixels. Supported range is 1 to 30,000.
		'''
		self.width = self.readInt()
		self.logger.debug("Width: %d" % self.width)
		validate("Width", self.width, range=self.SIZE_RANGE)

		'''
		2 bytes.
		Depth: The number of bits per channel. Supported values are 1, 8, and 16.
		'''
		self.depth = self.readShortInt() #TODO 1, 8, 16 .check for new versions
		self.logger.debug("Color Depth: %d" % self.depth)
		validate("Depth", self.depth, list=self.DEPTH_LIST)

		'''
		2 bytes.
		Color Mode: The color mode of the file. 
		'''
		colorModeMap = {0:"Bitmap", 1:"Grayscale", 2:"Indexed Color", 
						   3:"RGB Color", 4:"CMYK Color", 7:"Multichannel", 
						   8:"Duotone", 9:"Lab Color"}
		colorMode = self.readShortInt()
		self.colorMode = self.getCodeLabelPair(colorMode, colorModeMap)
		
		self.logger.debug("Color Schema: %s" % self.colorMode)

	def __str__(self):
		return  ("==Header==\nSignature: %s\n"
				"Version: %s\n"
				"Channels #: %s\n"
				"Height: %s\n"
				"Width: %s\n"
				"Depth: %s\n"
				"Color Mode: %s" % 
				(self.signature, self.version, self.channelsNum, self.height,
							self.width, self.depth, self.colorMode))



class PSDColorMode(PSDParserBase):
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

	def __init__(self, stream, psd):
		self.logger = logging.getLogger("pypsd.sections.PSDColorMode")
		self.debugMethodInOut("__init__")
		
		self.data = None
		
		super(PSDColorMode, self).__init__(stream, psd)
		
		
	def parse(self):
		self.debugMethodInOut("parse")
		
		'''
		4 bytes.
		Length: The length of the following color data.
		'''
		self.skipIntSize() #TODO Process color table

	def __str__(self):
		return "==Color Mode=="


class PSDImageResources(PSDParserBase):
	'''
	The third section of the file contains image resources. As with
	the color mode data, the section is indicated by a length field
	followed by the data.
	'''

	def __init__(self, stream, psd):
		self.logger = logging.getLogger("pypsd.sections.PSDImageResources")
		self.debugMethodInOut("__init__")

		super(PSDImageResources, self).__init__(stream, psd)


	def parse(self):
		self.debugMethodInOut("parse")
		
		'''
		4 bytes
		Length of image resource section.
		'''
		length = self.readInt()
		pos = self.getPos()
		
		'''
		Image resources
		'''
		self.resources = []
		while self.getPos() < pos + length:
			'''
			2 bytes
			Signature: '8BIM'
			'''
			sign = self.readString(4)
			validate("Image Resource block signature", sign, mustBe=self.SIGNATIRE_8BIM)
			'''
			2 bytes
			Unique identifier for the resource. Table 1.6 contains a list of resource
			IDs used by Photoshop.
			'''
			resId = self.readShortInt()
			'''
			Name: Pascal string, padded to make the size even (a null name
			consists of two bytes of 0)
			'''
			name = self.readPascalString()
			resource = {"id": resId, "name": name, "data":None}
			
			'''
			4 bytes
			Actual size of resource data that follows
			'''
			data_length = self.readInt(returnEven=True)
			data_start = self.getPos()
			
			'''
			The resource data, described in the sections on the individual resource
			types. It is padded to make the size even.
			'''
			
			if resId == 1050: #Slices
				slice_data = {}
				'''
				4 bytes.
				Version ( = 6)
				'''
				ver = self.readInt()
				validate("Photoshop Version for slices", ver, mustBe=6)
				
				'''
				4 * 4 bytes.
				Bounding rectangle for all of the slices: top, left, bottom, right of all the slices
				'''
				slice_data["rectangle"] = self.getRectangle()
				'''
				Name of group of slices: Unicode string
				'''
				slice_data["group_name"] = self.readUnicodeString()
				'''
				4 bytes.
				Number of slices to follow.
				'''
				slices_num = self.readInt()
				slices = [{}] * slices_num 
				for i in range(slices_num):
					slice = {}
					''' 4 bytes. ID'''
					slice["id"] = self.readInt()
					''' 4 bytes. Group ID'''
					slice["group_id"] = self.readInt()
					''' 4 bytes. Origin'''
					slice["origin"] = self.readInt()
					''' 4 bytes. Origin'''
					if slice["origin"] == 1:
						'''
						4 bytes.
						Associated Layer ID
						NOTE: Only present if Origin = 1
						'''
						slice["assoc_layer_id"] = self.readInt()
					''' Name: Unicode string '''
					slice["name"] = self.readUnicodeString()
					''' 4 bytes. Name '''
					slice["type"] = self.readInt()
					'''
					4 * 4 bytes.
					Left, top, right, bottom positions
					'''
					slice["position"] = self.getRectangle()
					'''
					Unicode Strings: Url, Target, Message, Alt Tag
					'''
					slice["URL"] = self.readUnicodeString()
					slice["target"] = self.readUnicodeString()
					slice["message"] = self.readUnicodeString()
					slice["alt"] = self.readUnicodeString()
					''' 1 byte. Cell text is HTML: Boolean'''
					slice["cell_is_HTML"] = self.readBoolean()
					''' Unicode. Cell text: Unicode string'''
					slice["cell_text"] = self.readUnicodeString()
					''' 4 bytes. Horizontal alignment'''
					slice["hor_align"] = self.readInt()
					''' 4 bytes. Vertical alignment'''
					slice["ver_align"] = self.readInt()
					slice["argb"] = [self.readTinyInt() for a in range(4)]
					
					slices[i] = slice
			
			self.resources.append(resource)
			
			self.skipRest(data_start, data_length)
		self.skipRest(pos, length)

	def __str__(self):
		return "==Image Resources=="


class PSDLayerMask(PSDParserBase):
	'''
	The fourth section contains information about Photoshop 3.0 layers
	and masks.
	If there are no layers or masks, this section is just 4 bytes:
	the length field, which is set to zero.
	'''

	def __init__(self, stream, psd):
		self.logger = logging.getLogger("pypsd.sections.PSDLayerMask")
		self.debugMethodInOut("__init__")

		self.layers = []

		super(PSDLayerMask, self).__init__(stream, psd)

	def parse(self):
		self.debugMethodInOut("parse")
		
		'''
		4 bytes.
		Length of the layer and mask information section.
		'''
		layerMaskSize = self.readInt()
		pos = self.getPos()
		
		if layerMaskSize > 0:
			'''
			4 bytes.
			Length of the layers info section, rounded up to a multiple of 2. 
			'''
			layerInfoSize = self.readInt(returnEven=True)
			
			if layerInfoSize > 0:
				'''
				2 bytes.
				Layers count.
				'''
				layersCount = self.readShortInt()

				'''
				If it is a negative number, its absolute value is the number of
				layers and the first alpha channel contains the transparency data for the
				merged result.
				'''
				if layersCount < 0:
					#TODO Process this if needed.
					layersCount = abs(layersCount)

				for i in range(layersCount):
					layer = PSDLayer(self.stream, self.psd)
					self.layers.append(layer)
					self.logger.debug(layer)
				
				for layer in self.layers:
					layer.getImageData(needReadPlaneInfo=True, lineLengths=[]) 
				
				self.layers.reverse()
			
			self.skipRest(pos, layerMaskSize)
		
		baseLayer = PSDLayer(self.stream, self.psd, is_base_layer=True)
		rle = self.readShortInt() == 1
		height = baseLayer.rectangle["height"]
		if rle:
			nLines = height * len(baseLayer.channelsInfo)
			lineLengths = []
			for h in range(nLines):
				lineLength = self.readShortInt()
				lineLengths.append(lineLength)
			baseLayer.getImageData(False, lineLengths)
		else:
			baseLayer.getImageData(False)
		
		if not self.layers:
			self.layers.append(baseLayer)
		
	
	def groupLayers(self):
		parents = [None]
		for layer in self.layers:
			layer.parent = parents[-1]
			layer.parents = parents[1:]
			if layer.layerType["code"] == 0:
				pass
			elif layer.layerType["code"] == 3:
				del parents[-1]
			else:
				parents.append(layer)
	
		
	def __str__(self):
		return "==Layer Mask==\n"



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
	def __init__(self, stream, psd, is_base_layer=False):
		self.logger = logging.getLogger("pypsd.sections.PSDLayer")
		self.debugMethodInOut("__init__")

		self.is_base_layer = is_base_layer
		'''Channel information. list(tuple(channelId, Length))'''
		self.channelsInfo = []
		'''Blend mode key. blendMode.code, blendMode.label'''
		self.blendMode = {}
		'''Opacity. 0 = transparent ... 255 = opaque'''
		self.opacity = None
		'''Clipping. false = base, true = non-base'''
		self.clipping = None
		
		self.transpProtected = None
		self.visible =  None
		self.obsolete = None
		'''Pixel data irrelevant to appearance of document'''
		self.pixelDataIrrelevant = None
		
		'''Layer name'''
		self.name = None
		
		'''Channel image data. {"a":[],"r":[],"g":[],"b":[]}'''
		self.channels = {}
		
		self.layerId = None
		self.layerType = {"code":0, "label":"other"}
		self.parent = None
		self.saved = False
		self.text = None
		
		super(PSDLayer, self).__init__(stream, psd)
	
	def parse(self):
		self.debugMethodInOut("parse")
		
		if self.is_base_layer:
			return self.parse_base_layer()
		
		'''
		4 * 4 bytes.
		Rectangle containing the contents of the layer. Specified as top, left,
		bottom, right coordinates.
		'''
		self.rectangle = self.getRectangle()

		'''
		2 bytes.
		The number of channels in the layer.
		'''
		chanelsCount = self.readShortInt()

		'''
		6 * number of channels bytes
		Channel information. Six bytes per channel.
		'''
		self.channelsInfo = []
		for i in range(chanelsCount):
			channelId = self.readShortInt()
			channelLength = self.readInt()
			self.channelsInfo.append((channelId, channelLength))


		'''
		4 bytes.
		Blend mode signature. 
		'''
		bimSignature = self.readString(4)
		validate("Blend mode signature", bimSignature, mustBe=self.SIGNATIRE_8BIM)

		'''
		4 bytes.
		Blend mode key.
		'''
		blendMap = {"norm":"normal",  "dark":"darken", "lite":"lighten",
					"hue":"hue", "sat":"saturation", "colr":"color",
					"lum":"luminosity", "mul":"multiply", "scrn":"screen",
					"diss":"dissolve", "over":"overlay", "hLit":"hard light",
					"sLit":"soft light", "diff":"difference","smud":"exclusion",
					"div ":"color dodge", "idiv":"color burn", 
					"lbrn":"linear burn", "lddg":"linear dodge", 
					"vLit":"vivid light", "lLit":"linear light", 
					"pLit":"pin light", "hMix":"hard mix"}
		blendCode = self.readString(4).strip()
		self.blendMode = self.getCodeLabelPair(blendCode, blendMap)
		validate("Blend mode key", blendCode, list=blendMap.keys())

		'''
		1 byte.
		Opacity. 0 = transparent ... 255 = opaque
		'''
		self.opacity = self.readTinyInt()
		validate("Opacity", self.opacity, range=self.OPACITY_RANGE)

		'''
		1 byte.
		Clipping. 0 (false) = base, 1 (true) = non-base
		'''
		self.clipping = self.readTinyInt() != 0

		'''
		1 byte.
		bit 0 = transparency protected 
		bit 1 = visible
		bit 2 = obsolete
		bit 3 = 1 for Photoshop 5.0 and later, tells if bit 4 has useful information;
		bit 4 = pixel data irrelevant to appearance of document
		'''
		flagsBits = self.readBits(1)
		self.transpProtected = flagsBits[0] != 0
		self.visible =  flagsBits[1] == 0
		self.obsolete =  flagsBits[2] != 0
		'''bit 3 = 1 for Photoshop 5.0 and later, tells if bit 4 has useful 
		information'''
		if flagsBits[3] != 0:
			self.pixelDataIrrelevant = flagsBits[4] != 0 
		
		'''
		1 bytes.
		Filler (zero).
		'''
		validate("Filler (zero)", self.readTinyInt(), mustBe=0)
		
		# ---- Extra Fields Parsing.
		
		'''
		4 bytes.
		Extra data field.
		'''
		extraFieldsSize = self.readInt()
		pos = self.getPos()
		
		self.readLayerMask()
				
		'''
		4 bytes.
		Length of layer blending ranges data
		'''
		self.skipIntSize()    
		
		'''
		Variable.
		Layer name: Pascal string, padded to a multiple of 4 bytes.
		'''
		self.name = self.readPascalString()
		self.logger.debug([self.name])
		
		prevPos = self.getPos()
		while self.getPos() - pos < extraFieldsSize:
			bimSignature = self.readString(4)
			validate("Blend mode signature", bimSignature, mustBe=self.SIGNATIRE_8BIM)
			'''
			4 bytes.
			Key: a 4-character code
			'''
			tag = self.readString(4)
			
			'''
			4 bytes.
			Length data below, rounded up to an even byte count.
			'''
			size = self.readInt(True) 
			prevPos = self.getPos()
			
			if tag == "lyid":
				'''
				Layer ID
				'''
				self.layerId = self.readInt()
			
			elif tag == "shmd":
				'''
				Metadata setting
				'''
				self.readMetadata()

			elif tag == "lsct":
				'''
				Section divider setting
				'''
				self.readLayerSectionDevider()
			elif tag == 'luni':
				'''
				Unicode Name
				'''
				self.name = self.readUnicodeString()
			elif tag == "vmsk":
				'''
				Vector Mask
				'''
				self.readVectorMask()
			elif tag == 'TySh':
				self.readTypeTool()
				self.text = self.text_data["Txt"]["value"]
			
			self.skipRest(prevPos, size)
		 
		self.skipRest(pos, extraFieldsSize)	
	
	def readTypeTool(self):
		ver = self.readShortInt()
		transforms = [0]*6
		for i in range(6):
			transforms[i] = self.readDouble()
		text_ver = self.readShortInt()
		descr_ver = self.readInt()
		if ver != 1 or text_ver != 50 or descr_ver != 16:
			return
		text_data = self.readDescriptorStructure()
		
		wrap_ver = self.readShortInt()
		descr_ver = self.readInt()
		wrap_data = self.readDescriptorStructure()
		rectangle = [0]*4
		for i in range(4):
			rectangle[i] = self.readDouble()
		self.text_data = text_data
		self.wrap_data = wrap_data
		styled_text = []
		#try:
		
		def getSafeFont(font):
			safe_font_list = ["Arial", "Courier New", "Georgia", "Times New Roman",
							"Verdana", "Trebuchet MS", "Lucida Sans", "Tahoma"]
			for safe_font in safe_font_list:
				it = True
				for word in safe_font.split(" "):
					if not word in font:
						it = False
				if it:
					return safe_font

			return font
		
		ps_dict = self.text_data["EngineData"]["value"]
		text = ps_dict["EngineDict"]["Editor"]["Text"]
		style_run = ps_dict["EngineDict"]["StyleRun"]
		styles_list = style_run["RunArray"]
		styles_run_list = style_run["RunLengthArray"]
		
		fonts_list = ps_dict["DocumentResources"]["FontSet"]
		start = 0
		for i, style in enumerate(styles_list):
			st = style["StyleSheet"]["StyleSheetData"] 
			end = int(start + styles_run_list[i])
			font_i = st["Font"]
			font_name=fonts_list[font_i]["Name"]
			safe_font_name = getSafeFont(font_name)
			color = tuple([int(255*j) for j in st["FillColor"]["Values"]][1:])
			
			line_height = "Auto" if st["Leading"] == 1500 else st["Leading"]
			piese = text[start:end]
			styled_text.append({'text': piese,
							    'style':{
									'font': safe_font_name,
									'size': st["FontSize"],
									'color': "#%02X%02X%02X" % color,
									'underline': st["Underline"],
									'allCaps': st["FontCaps"],
									'italic': "Italic" in font_name or st["FauxItalic"],
									'bold': "Bold" in font_name or st["FauxBold"],
									'letterSpacing': st["Tracking"] / 20,
									'lineHeight': line_height,
									'paragraphEnds': piese[-1] in ["\n", "\r"],
								}})
			start += styles_run_list[i]
		self.styled_text = styled_text
		#except:
		#	pass
	
	def readVectorMask(self):
		version = self.readInt()
		flags = self.readBits(4)
		#TODO Read PAth Information
		pass
	
	def readLayerMask(self):
		'''
		4 bytes.
		Size of the data: 36, 20, or 0.
		If zero, the following fields are not present
		'''
		size = self.readInt()
		validate("Size of the data", size, list=[36, 20, 0])
		if size == 0:
			return
		
		self.maskRectangle = self.getRectangle()
		maskDefaultColor = self.readTinyInt()
		flagsBits = self.readBits(1)
		if size == 20:
			self.maskPadding = self.readShortInt()
		else:
			realFlags = self.readTinyInt()
			realUserMaskBack = self.readTinyInt()
			maskRectangle2 = self.getRectangle()
	
	def parse_base_layer(self):
		header = self.psd.header
		height = header.height
		width = header.width
		self.rectangle = {"top":0, "left":0, 
				  		  "bottom":height, "right":width, 
    		              "width":width, "height":height}
		
		channels = header.channelsNum
		chanDelta= 3 - channels
		#If channels = 3, then [0,1,2] if channels = 4, than [-1,0,1,2]
		self.channelsInfo = [(i, 0) for i in range(chanDelta, channels+chanDelta)]
		
		self.blendMode = {"code":"norm", "label":"normal"}
		
		self.opacity = 255
		self.visible = True
		
		self.name = 'Canvas'
		self.layerId = 0
		
	
	def readMetadata(self):
		'''
		4 bytes.
		Count of metadata items to follow
		'''
		metaCount = self.readInt()
		for i in range(metaCount):
			'''
			4 bytes.
			Signature of the data
			'''
			bimSignature = self.readString(4)
			validate("Meta Data Signature", bimSignature, mustBe=self.SIGNATIRE_8BIM)
			'''
			4 bytes.
			Key of the data
			'''
			key = self.readString(4)
			validate("Key for metadata", list=["mlst"])
			'''
			1 bytes. Copy on sheet duplication
			3 bytes. Padding
			'''
			self.skip(4)
			size = self.readInt()
			pos = self.getPos()
			
			if key == "mlst":
				pass
				#TODO readAnimation .. later
			
			self.skipRest(pos, size)
	
	
	def readLayerSectionDevider(self):
		'''
		4 bytes.
		Type. 4 possible values, 
		0 = any other type of layer, 
		1 = open "folder", 
		2 = closed "folder", 
		3 = bounding section divider, hidden in the UI
		'''
		typesMap = {0:"other", 1:"open folder", 2:"closed folder", 
				    3:"bounding section divider"}
		typeCode = self.readInt()
		self.layerType = self.getCodeLabelPair(typeCode, typesMap)
	
	
	def getImageData(self, needReadPlaneInfo=True, lineLengths=[]):
		'''
		Channel image data. Contains one or more image data records for each 
		layer. The layers are in the same order as in the layer information.
		'''
		self.channels = {"a":[],"r":[],"g":[],"b":[]}
		opacity_devider = self.opacity / 255
		for i, channelTuple in enumerate(self.channelsInfo):
			channelId, length = channelTuple
			if channelId < -1:
				width = self.maskRectangle["width"]
				height = self.maskRectangle["height"]
			else:
				width = self.rectangle["width"]
				height = self.rectangle["height"]
				
			channel = self.readColorPlane(needReadPlaneInfo, lineLengths, i, height=height, width=width)
			if channelId == -1:
				self.channels["a"] = [int(ch * opacity_devider) for ch in channel]  
			elif channelId == 0:
				self.channels["r"] = channel
			elif channelId == 1:
				self.channels["g"] = channel
			elif channelId == 2:
				self.channels["b"] = channel
			elif channelId < -1:
				self.channels["a"] = [int(a * (c/255)) for a, c in zip(self.channels["a"], channel)]
				
		self.debugMethodInOut("getImageData", 
							  invars={"needReadPlaneInfo":needReadPlaneInfo,
									  "lineLengths":lineLengths})
		self.makeImage()
		#self.makePngImage()
		
				
	def readColorPlane(self, needReadPlaneInfo=True, lineLengths=[], planeNum=-1, height=None, width=None):
		self.debugMethodInOut("readColorPlane")

		size = width  * height
		imageData = []
		rleEncoded = None
		
		if needReadPlaneInfo:
			'''
			2 bytes.
			Compression. 
			0 = Raw Data, 
			1 = RLE compressed, 
			2 = ZIP without prediction, 
			3 = ZIP with prediction.
	  		'''
			compression = self.readShortInt()
			validate("Compression", compression, range=[0,3])
		
			'''
			If the compression code is 1, the image data starts with the byte 
			counts for all the scan lines in the channel (LayerBottom LayerTop), 
			with each count stored as a two byte value.
			'''	
			rleEncoded = compression == 1 
			if rleEncoded: #RLE compressed
				if not lineLengths:
					lineLengths = [self.readShortInt() for a in range(height)]
			planeNum = 0
			#TODO raise NotImplementedError("Zip compression is not working yet.")
		else:
			rleEncoded = lineLengths != []
		
		if rleEncoded:
			imageData = self.readPlaneCompressed(lineLengths, planeNum, h=height, w=width)
		else:
			imageData = self.readBytesList(size)
		
		return imageData
	
	def readPlaneCompressed(self, lineLengths, planeNum, h=None, w=None):
		b = [0] * (w*h)
		s = [] #w * 2
		pos = 0
		lineIndex = planeNum * h
		for i in range(h):
			len = lineLengths[lineIndex]
			lineIndex += 1
			s = self.readBytesList(len) + [0] * (w * 2 - len)
			self.decodeRLE(s, 0, len, b, pos) 
			pos += w
		
		return b
	
	def decodeRLE(self, src, sindex, slen, dst, dindex):
		#try:
		max = sindex + slen
		while sindex < max:
			b = src[sindex]
			sindex += 1
			n = b
			if b > 127:
				n = 255 - n + 2
				b = src[sindex]
				sindex += 1
				for i in range(n):
					dst[dindex] = b
					dindex += 1
			else:
				n = n + 1
				dst[dindex:dindex+n] = src[sindex:sindex+n]
				dindex += n
				sindex += n
		#except Exception:
		#	raise BaseException("RLE Decoding fatal error.")

	def makeImage(self):
		width = self.rectangle["width"] 
		height = self.rectangle["height"]
		
		self.image = Image.new("RGBA", (width, height))
		imageData = [0]* (height * width)
		white_rgba = [255] * 4
		rgba_letters = ["r", "g","b","a"]
		rgba_on_arr = [ len(self.channels[c]) for c in rgba_letters]
				
		for i in range(height * width):
			rgba = [255] * 4
			for j, c in enumerate(rgba_letters):
				if rgba_on_arr[j] > i:
					rgba[j] = self.channels[c][i]
			imageData[i] = tuple(rgba)
		
		self.image.putdata(imageData)
		
#		for i, a in enumerate(self.channels["a"]):
#			r = self.channels["r"][i]
#			g = self.channels["g"][i]
#			b = self.channels["b"][i]
#			rgba = (r,g,b,a)
#			imageData.append(rgba)
		        
		
		
#	def makePngImage(self):
#		width = self.rectangle["width"] 
#		height = self.rectangle["height"]
#		if width == 0 or height == 0:
#			return
#		 
#		png_writer = png.Writer(width=width, 
#							   height=height, 
#							   greyscale=False, 
#							   alpha=True, 
#							   bitdepth = 8, #TODO HardCode. Take from Header.
#							   )
#		pixelsData = []
#		for i in range(height * width):
#			for c in ["r", "g","b","a"]:
#				pixelsData += [self.channels[c][i]] if len(self.channels[c]) > i else [255]
#		
#		buffer = StringIO.StringIO()
#		png_writer.write_array(buffer, pixelsData)
#		self.image = buffer.getvalue()
#		
#		buffer.close()

	
	def __str__(self):
		return ("\n=== Layer - %s ===\n"
			    "Parent: %s\n"
			   "Id: %d\n"
			   "Type: %s\n"
		       "Opacity: %d\n"
		       "Rectangle:\n"
		       "\theight, width: %d, %d\n"
		       "\ttop, left: %d, %d\n"
		       "Visible: %s\n"
		       "Obsolete: %s\n"
	           "Clipping: %s\n"
	           "Transporent Protected: %s\n" 
	           "Pixel Data Irrelevant: %s\n"
	           "Channels Info: %s\nBlend Mode: %s" % 
	           (self.name, (self.parent.layerId if self.parent else "None"), 
			    self.layerId, self.layerType,
			    self.opacity, self.rectangle["height"], 
			    self.rectangle["width"], self.rectangle["top"], 
			    self.rectangle["left"], self.visible, self.obsolete,
			    self.clipping, self.transpProtected, self.pixelDataIrrelevant,
			    self.channelsInfo, self.blendMode))
