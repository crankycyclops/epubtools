# -*- coding: utf-8 -*-

import re
import util, driver

class Abiword(driver.Driver):

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, coverPath, tmpLocation = '/tmp'):
		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, coverPath, tmpLocation)

	##########################################################################

	def openDriver(self):

		# TODO
		pass

	##########################################################################

	# Processes a chapter from any document type that Abiword can read (.doc,
	# .docx, .rtf, etc.) and transforms it into ePub friendly XHTML.
	def transformChapter(self, inputText):

		# TODO
		return {
			'chapter': '',
			'chapterSlug': '',
			'text': inputText
		}

	##########################################################################

	def processChaptersList(self, inputPath, chapters):

		# TODO
		pass

