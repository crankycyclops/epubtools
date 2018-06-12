# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

# Input driver base class
class Driver:

	__metaclass__ = ABCMeta

	##########################################################################

	# Constructor
	def __init__(self):

		# List of chapters processed. In the Epub output driver, this data will
		# be used to create the manifest.
		self.__chapterLog = []

		# Points to self.chapterLog, the root of the table of contents, by
		# default. However, if we're currently parsing chapters inside of a part
		# (a group of chapters with its own title), this will point to a nested
		# array within self.chapterLog representing that group of chapters.
		# This makes it easy to add chapters to the right place as we parse the
		# input document.
		self.__curTOCPart = self.__chapterLog

		# Used to enumerate chapter files
		self.__curChapterIndex = 1

		# After running self.parse(), this will contain a DOM-like representation
		# of the input document
		

	##########################################################################

	# Opens the input source for reading and throws an exception if opening
	# the document failed. If a driver needs to do more than what this method
	# does, then it should override this function and call super().open().
	def open(self, filename):

		self.__inputPath = filename

	##########################################################################

	# Parse the input document into a DOM-like representation and return it,
	# along with the contents of self.chapterLog, so that the output driver can
	# work its black voodoo magic.
	# TODO: detail the DOM structure in more detail
	@abstractmethod
	def parse(self):

		pass

	##########################################################################

	# Cleans up after parsing is complete. If there's no cleanup to do for a
	# particular driver, just implement an empty function.
	@abstractmethod
	def cleanup(self):

		pass

