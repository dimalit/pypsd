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

		with open(self.fileName, mode = 'rb') as f:
			self.logger.debug("File size is: %d bytes" %
							os.path.getsize(self.fileName))

			self.header = PSDHeader(f)
			self.logger.debug("Header:\n%s" % self.header)

			self.colorMode = PSDColorMode(f)
			self.logger.debug("Color mode:%s" % self.colorMode)

			self.imageResources = PSDImageResources(f)

			self.layerMask = PSDLayerMask(f)

			#self.imageData = PSDImageData(f)

	def __str__(self):
		return ("File Name:%s\n%s\n%s\n%s\n%s\n%s" %
			(self.fileName,
				self.header,
				self.colorMode,
				self.imageResources,
				self.layerMask,
				self.imageData))
