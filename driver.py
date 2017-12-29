# -*- coding: utf-8 -*-

import shutil, re, os, binascii
from abc import ABCMeta, abstractmethod

import util

class Driver(object):

	__metaclass__ = ABCMeta
	scriptPath = os.path.dirname(os.path.realpath(__file__))

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation = '/tmp'):

		# List of chapters processed. Used to create the manifest.
		self.chapterLog = []

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

		# Where we write temporary files
		self.tmpLocation = tmpLocation

		# Generate a unique ID that can be used in /tmp to avoid collisions
		# during concurrently running instances. Also used in the creation
		# of the book's UID.
		self.uid = str(binascii.hexlify(os.urandom(16))).replace("'", '')[1:]
		self.tmpOutputDir = self.tmpLocation + '/' + self.uid

		# Used to enumerate chapter files
		self.curChapterIndex = 1

		# Setup template variables
		self.initTemplateVars()

	##########################################################################

	# Template variables used to fill in various data fields in the ePub's files.
	def initTemplateVars(self):

		invalidAlphaNumRegex = re.compile('[^a-zA-Z0-9]')

		authorSlug = invalidAlphaNumRegex.sub('', self.bookAuthor.lower())
		titleSlug = invalidAlphaNumRegex.sub('', self.bookTitle.lower())

		# Variables to implement after processing chapters (in self.initChaptersTemplateVars):
		# %firstChapterFilename, %chapterManifestEntries, %chapterSpineEntries, %chapterTocEntries, %navmap
		self.templateVars = {
			'%uid': 'epub.' + titleSlug + '.' + authorSlug + '.' + self.uid,
			'%title': self.bookTitle,
			'%upperTitle': self.bookTitle.upper(),
			'%author': self.bookAuthor,
			'%autLastfirst': self.bookAuthor, #TODO: split on first whitespace and add comma
			'%publisher': self.bookPublisher,
			'%lang': self.bookLang,
			'%pubdate': self.pubDate,
			'%copyrightYear': self.copyrightYear,
			'%coverImageManifestEntry': '<item id="cover-image" href="Cover.jpg" media-type="image/jpeg" properties="cover-image" />'
		}

		# We may or may not want to include a separate automagically generated copyright page.
		if self.includeCopyright:

			self.templateVars['%copyrightPageManifestEntry'] = '<item id="copyright" media-type="application/xhtml+xml" href="copyright.xhtml" />'
			self.templateVars['%copyrightSpineEntry'] = '<itemref idref="copyright" linear="yes" />'
			self.templateVars['%copyrightTocEntry'] = '<li><a href="copyright.xhtml">Copyright Notice</a></li>'

			if self.isFiction:
				self.templateVars['%fictionCopyrightAddition'] = '\t\t\t\t<p style="text-indent: 0; margin-bottom: 1em; line-height: 100%;">\n\t\t\t\tThis book is a work of fiction. Any similarity between the characters and situations within its pages and places or persons, living or dead, is unintentional and coincidental.<br />\n\t\t\t\t</p>\n'
			else:
				self.templateVars['%fictionCopyrightAddition'] = ''

		else:
			self.templateVars['%copyrightPageManifestEntry'] = ''
			self.templateVars['%copyrightSpineEntry'] = ''
			self.templateVars['%copyrightTocEntry'] = ''
			self.templateVars['%fictionCopyrightAddition'] = '' # doesn't matter, b/c there's no copyright page ;)

	##########################################################################

	# Similiar to initTemplateVars, except that these variables depend on the
	# chapters having been processed first, which means we can't call this
	# in the constructor like we can in the other.
	def initChaptersTemplateVars(self):

		chapterManifestEntries = ''
		chapterSpineEntries = ''
		chapterTocEntries = ''
		navmap = ''
		playOrder = 2;

		if self.includeCopyright:
			navmap = (
				navmap + '\n\t\t<navPoint id="copyright" playOrder="' +
				str(playOrder) + '">\n' + '\t\t\t<navLabel>\n\t\t\t\t<text>\n' +
				'\t\t\t\t\tCopyright Notice\n\t\t\t\t</text>\n' +
				'\t\t\t</navLabel>\n\t\t\t<content src="copyright.xhtml" />\n' +
				'\t\t</navPoint>\n'
			)
			playOrder += 1

		navmap = (
			navmap + '\n\t\t<navPoint id="toc" playOrder="' + str(playOrder) + '">\n' +
			'\t\t\t<navLabel>\n\t\t\t\t<text>\n\t\t\t\t\tTable of Contents\n\t\t\t\t</text>\n' +
			'\t\t\t</navLabel>\n\t\t\t<content src="toc.xhtml" />\n\t\t</navPoint>\n'
		)
		playOrder += 1

		for chapter in self.chapterLog:

			chapterId = 'ch' + chapter['chapterSlug']
			chapterFilename = chapter['chapterSlug'] + '.xhtml'
			chapterManifestEntries = chapterManifestEntries + '\t\t<item id="' + chapterId + '" media-type="application/xhtml+xml" href="' + chapterFilename + '" />\n'
			chapterSpineEntries = chapterSpineEntries + '\t\t<itemref idref="' + chapterId + '" linear="yes" />\n'
			chapterTocEntries = chapterTocEntries + '\t\t\t\t\t<li><a href="' + chapterFilename + '">' + chapter['chapter'] + '</a></li>\n'
			navmap = (
				navmap + '\n\t\t<navPoint id="ch' + chapter['chapterSlug'] +
				'" playOrder="' + str(playOrder) + '">\n' +
				'\t\t\t<navLabel>\n\t\t\t\t<text>\n\t\t\t\t\t' + chapter['chapter'] + '\n\t\t\t\t</text>\n' +
				'\t\t\t</navLabel>\n\t\t\t<content src="' + chapterFilename + '" />\n\t\t</navPoint>\n'
			)
			playOrder += 1

		self.templateVars['%chapterManifestEntries'] = chapterManifestEntries
		self.templateVars['%chapterSpineEntries'] = chapterSpineEntries
		self.templateVars['%chapterTocEntries'] = chapterTocEntries
		self.templateVars['%navmap'] = navmap
		self.templateVars['%firstChapterFilename'] = self.chapterLog[0]['chapterSlug'] + '.xhtml'

	##########################################################################

	# Takes as input a template and spits out a fully reconstituted file using
	# the variables defined above.
	def hydrate(self, template):

		for var in self.templateVars.keys():
			template = template.replace(var, self.templateVars[var])

		return template

	##########################################################################

	# Every driver will open files a bit differently. This is the backend for
	# self.openInput.
	@abstractmethod
	def openDriver(self):
		pass

	##########################################################################

	# Opens the input source for reading and throws an exception if opening
	# the ZIP archive or directory failed.
	def openInput(self, inputFilename):

		self.inputPath = inputFilename
		self.openDriver()

	##########################################################################

	# Cleans up the mess left behind after an e-book conversion. Any methods
	# that override this should make sure to call super().cleanup().
	def cleanup(self):

		try:
			shutil.rmtree(self.tmpOutputDir)

		# If this is on the backend of a server, I don't want people to get
		# error messages about it. But /tmp should be monitored to make sure
		# it's not filling up because this is silently failing.
		except:
			pass

	##########################################################################

	# Creates a specially formatted ZIP file of the book's contents, per the
	# ePub specifications.
	def zipBook(self, outputFilename):

		try:

			if os.path.isfile(outputFilename):
				os.remove(outputFilename)

			util.zipdirs(self.tmpOutputDir + '/mimetype', outputFilename, self.tmpOutputDir, False)
			util.zipdirs([self.tmpOutputDir + '/META-INF', self.tmpOutputDir + '/OEBPS'], outputFilename, self.tmpOutputDir)

		except:
			raise Exception('Failed to write output file ' + outputFilename)

	##########################################################################

	# Transforms input text of a chapter into an ePub-friendly XHTML format.
	@abstractmethod
	def transformChapter(self, inputText):
		pass

	##########################################################################

	# Returns the beginning of a chapter XHTML file.
	def _getXHTMLHeader(self, sectionType, chapterHeading):

		# TODO: should xml:lang be set to whichever language the e-book is in,
		# and if so, how do I map that value?
		XHTMLHead  = '<?xml version="1.0" encoding="UTF-8"?>\n'
		XHTMLHead += '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" xmlns:epub="http://www.idpf.org/2007/ops">\n\n'

		XHTMLHead += '\t<head>\n'
		XHTMLHead += '\t\t<meta charset="utf-8" />\n'
		XHTMLHead += '\t\t<title>' + self.bookTitle + '</title>\n'
		XHTMLHead += '\t\t<link rel="stylesheet" href="style.css" type="text/css" />\n'
		XHTMLHead += '\t</head>\n\n'

		XHTMLHead += '\t<body>\n\n'
		XHTMLHead += '\t\t<!-- An EPUB 3 feature that degrades harmlessly in EPUB 2 -->\n'
		XHTMLHead += '\t\t<section epub:type="bodymatter '+ sectionType + '">\n\n'

		XHTMLHead += '\t\t\t<header>\n'
		XHTMLHead += '\t\t\t\t<h1>' + chapterHeading + '</h1>\n'
		XHTMLHead += '\t\t\t</header>\n\n'

		return XHTMLHead

	##########################################################################

	# Returns the end of a chapter XHTML file.
	def _getXHTMLFooter(self):

		XHTMLFoot  = '\t\t</section>\n\n'
		XHTMLFoot += '\t</body>\n\n'
		XHTMLFoot += '</html>'

		return XHTMLFoot

	##########################################################################

	# Defines a part of the book underwhich a group of chapters fall into.
	def processPart(self, partName):

		chapterFilename = self.tmpOutputDir + '/OEBPS/' + str(self.curChapterIndex).zfill(3) + '_' + re.compile('[^a-zA-Z0-9]').sub('', partName) + '.xhtml'
		outputXHTML  = self._getXHTMLHeader('part', partName)
		outputXHTML += self._getXHTMLFooter()

		open(chapterFilename, 'w').write(outputXHTML)
		self.curChapterIndex = self.curChapterIndex + 1

	##########################################################################

	# Frontend for transformation of a chapter into an ePub-friendly format.
	# Calls self.transform. Caller must be prepared to catch exceptions.
	def processChapter(self, inputText):

		chapterXHTML = self.transformChapter(inputText)

		if chapterXHTML:
			chapterFilename = self.tmpOutputDir + '/OEBPS/' + str(self.curChapterIndex).zfill(3) + '_' + chapterXHTML['chapterSlug'] + '.xhtml'
			open(chapterFilename, 'w').write(chapterXHTML['text'])
			self.chapterLog.append({
				'chapter': chapterXHTML['chapter'],
				'chapterSlug': chapterXHTML['chapterSlug']
			})
			self.curChapterIndex = self.curChapterIndex + 1

	##########################################################################

	# Iterates through a list of chapters and runs processChapter on each.
	@abstractmethod
	def processChaptersList(self, inputPath, chapters):
		pass

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

			containerTemplate = self.hydrate(open(self.scriptPath + '/templates/container.xml', 'r').read())

			try:
				open(self.tmpOutputDir + '/META-INF/container.xml', 'w').write(containerTemplate)
			except:
				raise Exception('Failed to write container.xml.')

		except:
			raise Exception('Failed to read container.xml template.')

		# Process chapters
		self.processChaptersList(self.inputPath)
		self.initChaptersTemplateVars()

		# Write out filled-in templates
		templates = ['style.css', 'book.opf', 'Cover.xhtml', 'toc.ncx', 'title.xhtml', 'toc.xhtml']
		if self.includeCopyright:
			templates.append('copyright.xhtml')

		for templateName in templates:

			try:

				template = self.hydrate(open(self.scriptPath + '/templates/' + templateName, 'r').read())

				try:
					open(self.tmpOutputDir + '/OEBPS/' + templateName, 'w').write(template)
				except:
					raise Exception('Failed to write ' + templateName + '.')

			except:
				raise Exception('Failed to read ' + templateName + ' template.')

		# Copy the cover (WARNING: should not exceed 1000 pixels in longest
		# dimension to avoid crashing older e-readers.)
		try:
			# TODO: actually do extensive validation of the image before just
			# blindly copying it over ;)
			shutil.copyfile(self.coverPath, self.tmpOutputDir + '/OEBPS/Cover.jpg')

		except:
			raise Exception('Could not copy cover.')

		# Finally, write the ePub file. Phew!
		self.zipBook(outputFilename)

