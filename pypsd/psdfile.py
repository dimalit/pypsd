import os
import unicodedata
import string
import logging
import logging.config

from sections import *

logging.config.fileConfig("%s/conf/logging.conf" % os.path.dirname(__file__))


validFilenameChars = "-_.() %s%s" % (string.ascii_letters, string.digits)

def make_valid_filename(path, layer_name, layer_id):
	old_layer_name = layer_name
	layer_name = layer_name.decode()
	cleanedFilename = unicodedata.normalize('NFKD', layer_name).encode('ASCII', 'ignore')
	layer_name = ''.join(c for c in cleanedFilename if c in validFilenameChars)

	#Replace old bad name of layer's name with good one in the path.
	#Replaces should be only last occurrence (should be filename)
	path = path[::-1].replace(old_layer_name[::-1], layer_name[::-1], 1)[::-1]

	if os.path.exists(path): #file Already Exists
		layer_name += str(layer_id)

	return layer_name


class PSDFile(object):
	'''
	Main class. Contains all information about PSD file.
	The file format for Photoshop 3.0 is divided into five major parts.
	- File Header
	- Color Mode Data
	- Image Resources
	- Layer and Mask Information
	- Image Data
	'''

	def __init__(self, fileName = None, stream = None):
		self.logger = logging.getLogger("pypsd.psdfile.PSDFile")
		self.logger.debug("__init__ method. In: fileName=%s" % fileName)

		self.stream = stream
		self.fileName = fileName

		self.header = None
		self.colorMode = None
		self.imageResources = None
		self.layerMask = None
		self.imageData = None

	def parse(self):
		'''
		Parse PDF file and fill all self field.
		'''
		if not self.stream:
			if self.fileName is None:
				raise BaseException("File Name not specified.")

			if not os.path.exists(self.fileName):
				raise IOError("Can't find file specified.")

		#2.6 with open(self.fileName, mode = 'rb') as stream:
		try:
			if not self.stream:
				stream = open(self.fileName, mode = 'rb')
			else:
				stream = self.stream

			stream.seek(0,2)
			streamsize = stream.tell()
			stream.seek(0)

			self.logger.debug("File size is: %d bytes" % streamsize)

			self.header = PSDHeader(stream)
			self.logger.debug("Header:\n%s" % self.header)

			self.colorMode = PSDColorMode(stream)
			self.logger.debug("Color mode:%s" % self.colorMode)

			self.imageResources = PSDImageResources(stream)
			self.logger.debug("Image Resources:%s" % self.imageResources)

			self.layerMask = PSDLayerMask(stream)
			self.logger.debug("Layer Masks:%s" % self.layerMask)

			self.layerMask.groupLayers()

			for l in self.layerMask.layers:
				self.logger.debug("Layer %s\t%d Parent %s" % (l.name, l.layerId,
					(l.parent.layerId if l.parent else "None")))
		finally:
			if not self.stream:
				stream.close()

	def save(self, dest=None, saveInvis=False, dirName=None):
		if not dest:
			dest = os.getcwd()

		if not dirName:
			psdBaseName = os.path.basename(self.fileName)
			psdFileName = os.path.splitext(psdBaseName)
			dirName = psdFileName[0] 

		dest = os.path.join(dest, dirName)

		if not os.path.exists(dest):
			os.mkdir(dest)

		os.chdir(dest)

		for layer in self.layerMask.layers:
			name = layer.name
			id = layer.layerId
			toSave = True
			type = layer.layerType["code"]
			if type != 0:
				toSave = False
				if type in [1, 2]:
					name = make_valid_filename("./%s" % name, name, id)
					subdir = "./%s" % name
					if not os.path.exists(subdir):
						os.mkdir(subdir)
					os.chdir(subdir)
				elif type == 3:
					os.chdir("./..")
			if not layer.visible and not saveInvis:
				toSave = False

			if sum(layer.image.size) == 0:
				toSave = False

			if toSave:
				layer.saved = True
				name = make_valid_filename("%s/%s.png" % (os.getcwd(), name), name, id)
				layer.name = name #if it changes until
				try:
					#buffer = layer.image
					#writer = open("%s/%s.png" % (dest, name), "wb")
					#writer.write(buffer)
					layer.image.save("%s/%s.png" % (os.getcwd(), name), "PNG")
				except SystemError:
					self.logger.error("Can't save %s layer." % name)
		return dirName

	def __str__(self):
		return ("File Name:%s\n%s\n%s\n%s\n%s\n%s" %
			(	"",
				self.header,
				self.colorMode,
				self.imageResources,
				self.layerMask,
				self.imageData))
