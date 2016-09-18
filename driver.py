# -*- coding: utf-8 -*-

import util
from abc import ABCMeta, abstractmethod

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
	def __init__(self, bookAuthor = '', bookTitle = ''):

		self.bookAuthor = bookAuthor
		if not self.bookAuthor:
			util.eprint('\nWarning: Book author is blank\n')

		self.bookTitle = bookTitle
		if not self.bookTitle:
			util.eprint('\nWarning: Book title is blank\n')

	##########################################################################

	# Main point of entry for processing files in an input directory and
	# transforming them into an ePub.
	@abstractmethod
	def processBook(self, inputDir):
		pass

	##########################################################################

	# Transforms input text of a chapter into an ePub-friendly XHTML format.
	@abstractmethod
	def transformChapter(self, inputText):
		pass

