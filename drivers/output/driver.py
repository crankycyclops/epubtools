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

		self.bookLang = bookLang
		if not self.bookLang:
			raise Exception('Book language is blank. (Example: "en-US")')

		self.bookPublisher = bookPublisher
		if not self.bookPublisher:
			raise Exception('Book publisher is blank.')

		self.bookAuthor = bookAuthor
		if not self.bookAuthor:
			raise Exception('Book author is blank.')

		self.bookTitle = bookTitle
		if not self.bookTitle:
			raise Exception('Book title is blank.')

		self.pubDate = pubDate
		if not self.pubDate:
			raise Exception('Publication date is blank. (Format: YYYY-MM-DD)')

		# Quick sanity check on the publication date (doesn't catch all errors, so user beware!)
		validPubDateRegex = re.compile('(\d{4})-(\d{2})-(\d{2})')
		pubDateValidator = validPubDateRegex.search(self.pubDate)

		if not pubDateValidator or int(pubDateValidator.group(2)) < 1 or int(pubDateValidator.group(2)) > 12 or int(pubDateValidator.group(3)) < 1 or int(pubDateValidator.group(3)) > 31:
			raise Exception('Invalid publication date. Must be YYYY-MM-DD.')

		self.copyrightYear = copyrightYear
		if not self.copyrightYear:
			raise Exception('Copyright year is blank.')

		self.coverPath = coverPath
		if not self.coverPath:
			raise Exception('Path to cover is required but missing.')

		self.includeCopyright = includeCopyright
		self.isFiction = isFiction

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

