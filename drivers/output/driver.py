# -*- coding: utf-8 -*-

import shutil, re, os
from abc import ABCMeta, abstractmethod

# Output driver base class
class Driver:

	__metaclass__ = ABCMeta
	scriptPath = os.path.dirname(os.path.realpath(__file__))

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath):

		self._bookLang = bookLang
		if not self._bookLang:
			raise Exception('Book language is blank. (Example: "en-US")')

		self._bookPublisher = bookPublisher
		if not self._bookPublisher:
			raise Exception('Book publisher is blank.')

		self._bookAuthor = bookAuthor
		if not self._bookAuthor:
			raise Exception('Book author is blank.')

		self._bookTitle = bookTitle
		if not self._bookTitle:
			raise Exception('Book title is blank.')

		self._pubDate = pubDate
		if not self._pubDate:
			raise Exception('Publication date is blank. (Format: YYYY-MM-DD)')

		# Quick sanity check on the publication date (doesn't catch all errors, so user beware!)
		validPubDateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})')
		pubDateValidator = validPubDateRegex.search(self._pubDate)

		if not pubDateValidator or int(pubDateValidator.group(2)) < 1 or int(pubDateValidator.group(2)) > 12 or int(pubDateValidator.group(3)) < 1 or int(pubDateValidator.group(3)) > 31:
			raise Exception('Invalid publication date. Must be YYYY-MM-DD.')

		self._copyrightYear = copyrightYear
		if not self._copyrightYear:
			raise Exception('Copyright year is blank.')

		self._coverPath = coverPath
		if not self._coverPath:
			raise Exception('Path to cover is required but missing.')

		self._includeCopyright = includeCopyright
		self._isFiction = isFiction

	##########################################################################

	# Writes the output to disk and throws an exception if the process fails.
	@abstractmethod
	def write(self, filename):

		pass

	##########################################################################

	# Cleans up after conversion is complete. If there's no cleanup to do for a
	# particular driver, just implement an empty function.
	@abstractmethod
	def cleanup(self):

		pass

