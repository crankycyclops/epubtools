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
	def __init__(self, bookAuthor, bookTitle, copyrightYear):

		self.bookAuthor = bookAuthor
		if not self.bookAuthor:
			raise Exception('Book author is blank.')

		self.bookTitle = bookTitle
		if not self.bookTitle:
			raise Exception('Book title is blank.')

		self.copyrightYear = copyrightYear
		if not self.copyrightYear:
			raise Exception('Copyright year is blank.')

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

	# Cleans up the mess left behind after an e-book conversion.	
	def cleanup(self):

		# TODO: cleanup /tmp directory containing filled in templates
		# TODO: if extracted ZIP file, remove contents from /tmp
		pass

	##########################################################################

	# Called by processBook whenever it encounters another directory inside
	# the parent.
	def processBookDir(self, dirname):

		# TODO: just skipping for now
		pass

	##########################################################################

	# Main point of entry for processing files in an input directory and
	# transforming them into an ePub. Provides a generic method that should
	# work for any input source that contains one chapter per file. Anything
	# more complicated will require the specific driver to implement its own
	# version.
	def processBook(self, outputFilename):

		# Process each chapter individually
		for dirEntry in self.inputDir:

			if (dirEntry.name == '.' or dirEntry.name == '..'):
				continue

			# Chapters might be organized into further subdirectories; don't miss them!
			elif (dirEntry.is_dir()):
				self.processBookDir(dirEntry.path)

			else:

				try:

					inputFile = open(dirEntry.path, 'r')
					inputText = inputFile.read()
					chapterXHTML = self.transformChapter(inputText)

					# TODO: write out result

				except:
					raise Exception('Could not process one or more chapters.')

	##########################################################################

	# Transforms input text of a chapter into an ePub-friendly XHTML format.
	@abstractmethod
	def transformChapter(self, inputText):
		pass

