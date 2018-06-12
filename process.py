# -*- coding: utf-8 -*-

class Process:

	##########################################################################

	# Constructor
	def __init__(self, inputDriver, outputDriver):

		self.__inputDriver = inputDriver
		self.__outputDriver = outputDriver

	##########################################################################

	# Tells the input driver to open the source for reading.
	def open(self, filename):

		self.__inputDriver.open(filename)

	##########################################################################

	# Transform the input document to the appropriate output format and write it
	# to the specified filename.
	def convert(self, filename):

		chapterData = self.__inputDriver.parse()
		self.__outputDriver.transform(chapterData)
		self.__outputDriver.write(filename)

	##########################################################################

	# Clean up after ourselves when we're finished.
	def cleanup():

		self.__inputDriver.cleanup()
		self.__outputDriver.cleanup()

