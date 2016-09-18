# -*- coding: utf-8 -*-

import os, binascii
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

	scriptPath = os.path.dirname(os.path.realpath(__file__))

	# List of chapters processed. Used to create the manifest.
	chapterLog = []

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, copyrightYear, includeCopyright, tmpLocation):

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

		self.copyrightYear = copyrightYear
		if not self.copyrightYear:
			raise Exception('Copyright year is blank.')

		# Where we write temporary files
		self.tmpLocation = tmpLocation

		# Generate a unique ID that can be used in /tmp to avoid collisions
		# during concurrently running instances. Also used in the creation
		# of the book's UID.
		self.uid = str(binascii.hexlify(os.urandom(16))).replace("'", '')[1:]
		self.tmpOutputDir = self.tmpLocation + '/' + self.uid

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

	# Frontend for transformation of a chapter into an ePub-friendly format.
	# Calls self.transform. Caller must be prepared to catch exceptions.
	def processChapter(self, filename):

		inputText = open(filename, 'r').read()
		chapterXHTML = self.transformChapter(inputText)
		chapterFilename = self.tmpOutputDir + '/OEBPS/' + chapterXHTML['chapterSlug'] + '.xhtml'
		open(chapterFilename, 'w').write(chapterXHTML['text'])
		self.chapterLog.append({
			'chapter': chapterXHTML['chapter'],
			'chapterSlug': chapterXHTML['chapterSlug']
		})

	##########################################################################

	# Called by processBook whenever it encounters another directory inside
	# the parent. Recursively enters subdirectories.
	def processChaptersDir(self, dirIterator):

		# Process each chapter individually
		for dirEntry in dirIterator:

			if (dirEntry.name == '.' or dirEntry.name == '..'):
				continue

			# Chapters might be organized into further subdirectories; don't miss them!
			elif (dirEntry.is_dir()):
				self.processChaptersDir(os.scandir(dirEntry.path))

			else:

				try:
					self.processChapter(dirEntry.path)

				except IOError:
					raise Exception('Failed to write one or more chapters.')

				except:
					raise Exception('Failed to process one or more chapters.')

	##########################################################################

	# Main point of entry for processing files in an input directory and
	# transforming them into an ePub. Provides a generic method that should
	# work for any input source that contains one chapter per file. Anything
	# more complicated will require the specific driver to implement its own
	# version.
	def processBook(self, outputFilename):

		# Create the book's directory structure
		try:
			os.mkdir(self.tmpOutputDir)
			os.mkdir(self.tmpOutputDir + '/OEBPS')
			os.mkdir(self.tmpOutputDir + '/META-INF')

		except:
			raise Exception('Failed to create temporary output directory.')


		# Write out the book's mimetype
		try:
			mimetypeFile = open(self.tmpOutputDir + '/mimetype', 'w')
			mimetypeFile.write('application/epub+zip')
			mimetypeFile.close()

		except:
			raise Exception('Failed to write mimetype.')


		# Write out XML container that identifies where the book's files are to be found
		try:

			containerTemplate = open(self.scriptPath + '/templates/container.xml', 'r').read()

			try:
				open(self.tmpOutputDir + '/META-INF/container.xml', 'w').write(containerTemplate)
			except:
				raise Exception('Failed to write container.xml.')

		except:
			raise Exception('Failed to read container.xml template.')


		# Write out stylesheet
		try:

			cssTemplate = open(self.scriptPath + '/templates/style.css', 'r').read()

			try:
				open(self.tmpOutputDir + '/OEBPS/style.css', 'w').write(cssTemplate)
			except:
				raise Exception('Failed to write style.css.')

		except:
			raise Exception('Failed to read style.css template.')


		# Process chapters
		self.processChaptersDir(self.inputDir)

	##########################################################################

	# Transforms input text of a chapter into an ePub-friendly XHTML format.
	@abstractmethod
	def transformChapter(self, inputText):
		pass

