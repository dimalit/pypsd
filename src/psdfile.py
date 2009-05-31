import os


import logging
import logging.config


from pypsd.sections import *

#logging.config.fileConfig("conf/logging.conf")

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

	def __init__(self, fileName = None):
		self.logger = logging.getLogger("pypsd.psdfile.PSDFile")
		self.logger.debug("__init__ method. In: fileName=%s" % fileName)
		self.header = None
		self.colorMode = None
		self.imageResources = None
		self.layerMask = None
		self.imageData = None

		self.fileName = fileName;

	def parse(self):
		'''
		Parse PDF file and fill all self field.
		'''
		if self.fileName is None:
			raise BaseException("File Name not specified.")

		if not os.path.exists(self.fileName):
			raise IOError("Can't find file specified.")

		with open(self.fileName, mode = 'rb') as stream:
			self.logger.debug("File size is: %d bytes" %
							os.path.getsize(self.fileName))

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
	
	def save(self, dest=None):
		if not dest:
			dest = os.getcwd()

		for layer in self.layerMask.layers:
			if layer.layerType == 0:
				name = layer.name
				try:
					image = layer.image
					image.save("%s/%s.png" % (dest, name), "PNG")
				except SystemError:
					self.logger.error("Can't save %s layer." % name)
	
	def __str__(self):
		return ("File Name:%s\n%s\n%s\n%s\n%s\n%s" %
			(self.fileName,
				self.header,
				self.colorMode,
				self.imageResources,
				self.layerMask,
				self.imageData))
