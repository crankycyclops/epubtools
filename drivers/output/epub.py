# -*- coding: utf-8 -*-

# Dimensions for auto-generated covers
GENERATED_COVER_WIDTH=1000
GENERATED_COVER_HEIGHT=1600

import shutil, re, os, binascii
from driver import Driver

class Epub(Driver):

	# Table of special characters that should be converted to their corresponding
	# XHTML entities
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

	# A regex that defines valid characters for a chapter or part ID
	invalidIdCharsRegex = re.compile('[^a-zA-Z0-9]')

	##########################################################################

	# Template variables used to fill in various data fields in the ePub's files.
	def __initTemplateVars(self):

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

	# Takes as input a template and spits out a fully reconstituted file using
	# the variables defined by self.__initTemplateVars.
	def __hydrate(self, template):

		for var in self.templateVars.keys():
			template = template.replace(var, self.templateVars[var])

		return template

	##########################################################################

	# Creates a specially formatted ZIP file of the book's contents, per the
	# ePub specifications.
	def __zipBook(self, filename):

		try:

			if os.path.isfile(filename):
				os.remove(filename)

			util.zipdirs(self.tmpOutputDir + '/mimetype', filename, self.tmpOutputDir, False)
			util.zipdirs([self.tmpOutputDir + '/META-INF', self.tmpOutputDir + '/OEBPS'], filename, self.tmpOutputDir)

		except:
			raise Exception('Failed to write output file ' + filename)

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, isFiction, coverPath)

		# Setup epub template variables
		self.__initTemplateVars()

		# Where we write temporary files
		self.tmpLocation = tmpLocation

		# Generate a unique ID that can be used in /tmp to avoid collisions
		# during concurrently running instances. The Epub driver will also use
		# this for the book's UID.
		self.uid = str(binascii.hexlify(os.urandom(16))).replace("'", '')[1:]
		self.tmpOutputDir = self.tmpLocation + '/' + self.uid

	##########################################################################

	# Writes the resulting EPUB to disk.
	def write(self, filename):

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

		### TODO: all the stuff between

		# Finally, write the ePub file. Phew!
		self.__zipBook(filename)

	##########################################################################

	# Cleans up the mess left behind after an e-book conversion.
	def cleanup(self):

		try:
			shutil.rmtree(self.tmpOutputDir)

		# If this is on the backend of a server, I don't want people to get
		# error messages about it. But /tmp should be monitored to make sure
		# it's not filling up because this is silently failing.
		except:
			pass

