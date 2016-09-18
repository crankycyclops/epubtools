# -*- coding: utf-8 -*-

import os
from abc import ABCMeta, abstractmethod

import util

class Driver(object):

	__metaclass__ = ABCMeta

	specialChars = {
		"’": "&#8217;", #rsquo
		"‘": "&#8216;", #lsquo
		"”": "&#8221;", #rdquo
		"“": "&#8220;", #ldquo
		"…": "&#8230;", #hellip
		"—": "&#8212;", #mdash
		"–": "&#8211;", #ndash
		"™": "&#8482;", #trade
		"©": "&#169;",  #copy
		"®": "&#174;"   #reg
	}

	##########################################################################

	# Constructor
	def __init__(self, bookAuthor, bookTitle):

		self.bookAuthor = bookAuthor
		if not self.bookAuthor:
			raise Exception('Book author is blank.')

		self.bookTitle = bookTitle
		if not self.bookTitle:
			raise Exception('Book title is blank.')

	##########################################################################

	# Opens the input source for reading and throws an exception if opening
	# the ZIP archive or directory failed.
	def openInput(self, inputFilename):

		# TODO: support ZIP archives by extracting first to /tmp
		try:
			self.inputDir = os.scandir(inputFilename) # Requires Python 3.5+

		except FileNotFoundError:
			raise Exception("Input directory '" + inputFilename + "' not found.")

		except:
			raise Exception("An error occurred while trying to open '" + inputFilename + ".'")

	##########################################################################

	# Main point of entry for processing files in an input directory and
	# transforming them into an ePub.
	@abstractmethod
	def processBook(self, outputFilename):
		pass

	##########################################################################

	# Transforms input text of a chapter into an ePub-friendly XHTML format.
	@abstractmethod
	def transformChapter(self, inputText):
		pass

