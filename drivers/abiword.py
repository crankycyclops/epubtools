# -*- coding: utf-8 -*-

import re, os, sys, subprocess
import util, driver

class Abiword(driver.Driver):

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, coverPath, tmpLocation)

		# Where we save the intermediate latex file
		try:
			self.latexPath = self.tmpOutputDir + '_input'
			os.mkdir(self.latexPath)
		except:
			raise Exception('Could not create temporary input directory. This is a bug.')

	##########################################################################

	# Note that we're supposed to set a value for chaptersList, but since we
	# don't really use it, the default value of False is good enough and we're
	#  not going to bother doing more with it.
	def openDriver(self):

		# Make sure the input file exists
		if not os.path.isfile(self.inputPath):
			raise Exception('Input file ' + self.inputPath + ' does not exist.')

	##########################################################################

	def cleanup(self):

		try:
			shutil.rmtree(self.latexPath)
			super().cleanup()

		# We should at least still try to let the base class run its cleanup.
		except:
			super().cleanup()

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

	# Makes an external call to abiword, which reads the input file and outputs
	# it as a latex file that we can parse much more easily.
	def processChaptersList(self, inputPath, chapters):

		try:
			output = subprocess.check_output(['abiword', self.inputPath, '--to=latex', '-o', self.latexPath + '/input.tex'])
			if output:
				raise Exception()

		except:
			raise Exception('Failed to convert input document. This is a bug.')

		# TODO
		sys.exit(1)
