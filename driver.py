# -*- coding: utf-8 -*-

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
	def __init__(self, bookTitle = ''):

		self.bookTitle = bookTitle
		if not self.bookTitle:
			util.eprint('\nWarning: Book title is blank\n')

	##########################################################################

	# Transforms input text into an ePub-friendly XHTML format.
	@abstractmethod
	def transform(self, inputText):
		pass

