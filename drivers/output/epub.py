# -*- coding: utf-8 -*-

# Dimensions for auto-generated covers
GENERATED_COVER_WIDTH=1000
GENERATED_COVER_HEIGHT=1600

import shutil, re, os, binascii

import util
from .driver import Driver
from exception import OutputException

scriptPath = os.path.dirname(os.path.realpath(__file__))

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

		authorSlug = invalidAlphaNumRegex.sub('', self._bookAuthor.lower())
		titleSlug = invalidAlphaNumRegex.sub('', self._bookTitle.lower())

		# Variables to implement after processing chapters (in self.initChaptersTemplateVars):
		# %firstChapterFilename, %chapterManifestEntries, %chapterSpineEntries, %chapterTocEntries, %navmap
		self.__templateVars = {
			'%uid': 'epub.' + titleSlug + '.' + authorSlug + '.' + self.__uid,
			'%title': self._bookTitle,
			'%upperTitle': self._bookTitle.upper(),
			'%author': self._bookAuthor,
			'%autLastfirst': self._bookAuthor, #TODO: split on first whitespace and add comma
			'%publisher': self._bookPublisher,
			'%lang': self._bookLang,
			'%pubdate': self._pubDate,
			'%copyrightYear': self._copyrightYear,
			'%coverImageManifestEntry': '<item id="cover-image" href="Cover.jpg" media-type="image/jpeg" properties="cover-image" />'
		}

		# We may or may not want to include a separate automagically generated copyright page.
		if self._includeCopyright:

			self.__templateVars['%copyrightPageManifestEntry'] = '<item id="copyright" media-type="application/xhtml+xml" href="copyright.xhtml" />'
			self.__templateVars['%copyrightSpineEntry'] = '<itemref idref="copyright" linear="yes" />'
			self.__templateVars['%copyrightTocEntry'] = '<li><a href="copyright.xhtml">Copyright Notice</a></li>'

			if self._isFiction:
				self.__templateVars['%fictionCopyrightAddition'] = '\t\t\t\t<p style="text-indent: 0; margin-bottom: 1em; line-height: 100%;">\n\t\t\t\tThis book is a work of fiction. Any similarity between the characters and situations within its pages and places or persons, living or dead, is unintentional and coincidental.<br />\n\t\t\t\t</p>\n'
			else:
				self.__templateVars['%fictionCopyrightAddition'] = ''

		else:
			self.__templateVars['%copyrightPageManifestEntry'] = ''
			self.__templateVars['%copyrightSpineEntry'] = ''
			self.__templateVars['%copyrightTocEntry'] = ''
			self.__templateVars['%fictionCopyrightAddition'] = '' # doesn't matter, b/c there's no copyright page ;)

	##########################################################################

	# Helper function that populates the template variable for the list of
	# chapters in the OPF and toc.ncx.
	def __insertChaptersIntoOPFAndTocNcx(self, playOrder, navmap, chapterList = None, tocTabs = '\t\t\t\t\t'):

		# Always start at the root
		if not chapterList:
			chapterList = self.__chapterLog

		chapterManifestEntries = ''
		chapterSpineEntries = ''
		chapterTocEntries = ''

		for chapter in chapterList:

			chapterId = 'ch' + chapter['chapterSlug'] + str(chapter['chapterIndex']).zfill(3)
			chapterFilename = str(chapter['chapterIndex']).zfill(3) + '_' + chapter['chapterSlug'] + '.xhtml'
			chapterManifestEntries = chapterManifestEntries + '\t\t<item id="' + chapterId + '" media-type="application/xhtml+xml" href="' + chapterFilename + '" />\n'
			chapterSpineEntries = chapterSpineEntries + '\t\t<itemref idref="' + chapterId + '" linear="yes" />\n'

			chapterTocEntries = chapterTocEntries + tocTabs + '<li>\n'
			chapterTocEntries = chapterTocEntries + tocTabs + '\t<a href="' + chapterFilename + '">' + chapter['chapter'] + '</a>\n'

			# If we're inside of a part and need to process the chapters that
			# are inside, do so now.
			if chapter['children']:
				subChapterResults = self.__insertChaptersIntoOPFAndTocNcx(playOrder, navmap, chapter['children'], tocTabs + '\t\t')
				playOrder = subChapterResults['playOrder']
				navmap = subChapterResults['navmap']
				chapterManifestEntries = chapterManifestEntries + subChapterResults['chapterManifestEntries']
				chapterSpineEntries = chapterSpineEntries + subChapterResults['chapterSpineEntries']
				chapterTocEntries = chapterTocEntries + tocTabs + '\t<ol style="list-style-type: none;">\n' + subChapterResults['chapterTocEntries'] + tocTabs + '\t</ol>\n'

			chapterTocEntries = chapterTocEntries + tocTabs + '</li>\n'

			navmap = (
				navmap + '\n\t\t<navPoint id="ch' + chapter['chapterSlug'] +
				str(chapter['chapterIndex']).zfill(3) +
				'" playOrder="' + str(playOrder) + '">\n' +
				'\t\t\t<navLabel>\n\t\t\t\t<text>\n\t\t\t\t\t' + chapter['chapter'] + '\n\t\t\t\t</text>\n' +
				'\t\t\t</navLabel>\n\t\t\t<content src="' + chapterFilename + '" />\n\t\t</navPoint>\n'
			)

			playOrder += 1

		return {
			'chapterManifestEntries': chapterManifestEntries,
			'chapterSpineEntries': chapterSpineEntries,
			'chapterTocEntries': chapterTocEntries,
			'navmap': navmap,
			'playOrder': playOrder
		}

	##########################################################################

	# Similiar to self.__initTemplateVars, except that these variables depend on
	# the chapters having been processed first, which means we can't call this
	# in the constructor like we can in the other.
	def __initChaptersTemplateVars(self):

		navmap = ''
		playOrder = 2;

		if self._includeCopyright:
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

		# Insert chapters into the OPF and toc.ncx chapter list variables.
		chapterEntries = self.__insertChaptersIntoOPFAndTocNcx(playOrder, navmap)

		self.__templateVars['%chapterManifestEntries'] = chapterEntries['chapterManifestEntries']
		self.__templateVars['%chapterSpineEntries'] = chapterEntries['chapterSpineEntries']
		self.__templateVars['%chapterTocEntries'] = chapterEntries['chapterTocEntries']
		self.__templateVars['%navmap'] = chapterEntries['navmap']
		self.__templateVars['%firstChapterFilename'] = str(self.__chapterLog[0]['chapterIndex']).zfill(3) + '_' + self.__chapterLog[0]['chapterSlug'] + '.xhtml'

	##########################################################################

	# Takes as input a template and spits out a fully reconstituted file using
	# the variables defined by self.__initTemplateVars.
	def __hydrate(self, template):

		for var in self.__templateVars.keys():
			template = template.replace(var, self.__templateVars[var])

		return template

	##########################################################################

	# Creates a specially formatted ZIP file of the book's contents, per the
	# ePub specifications.
	def __zipBook(self, filename):

		try:

			if os.path.isfile(filename):
				os.remove(filename)

			util.zipdirs(self.__tmpOutputDir + '/mimetype', filename, self.__tmpOutputDir, False)
			util.zipdirs([self.__tmpOutputDir + '/META-INF', self.__tmpOutputDir + '/OEBPS'], filename, self.__tmpOutputDir)

		except:
			raise OutputException('Failed to write output file ' + filename)

	##########################################################################

	# Returns the beginning of a chapter XHTML file.
	def _getXHTMLHeader(self, sectionType, chapterHeading, centerHeading = False):

		# TODO: should xml:lang be set to whichever language the e-book is in,
		# and if so, how do I map that value?
		XHTMLHead  = '<?xml version="1.0" encoding="UTF-8"?>\n'
		XHTMLHead += '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" xmlns:epub="http://www.idpf.org/2007/ops">\n\n'

		XHTMLHead += '\t<head>\n'
		XHTMLHead += '\t\t<meta charset="utf-8" />\n'
		XHTMLHead += '\t\t<title>' + self._bookTitle + '</title>\n'
		XHTMLHead += '\t\t<link rel="stylesheet" href="style.css" type="text/css" />\n'
		XHTMLHead += '\t</head>\n\n'

		XHTMLHead += '\t<body>\n\n'
		XHTMLHead += '\t\t<!-- An EPUB 3 feature that degrades harmlessly in EPUB 2 -->\n'
		XHTMLHead += '\t\t<section epub:type="bodymatter '+ sectionType + '">\n\n'

		XHTMLHead += '\t\t\t<header>\n'
		if centerHeading:
			XHTMLHead += '\t\t\t\t<h1 style="text-align: center; margin-top: 20%;">' + chapterHeading + '</h1>\n'
		else:
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

	# Utility function to recursively parse an RTFDOM paragraph node into XHTML.
	def __parseRTFDOMParagraph(self, paragraphNode, depth = 0):

		# Strikethrough command relies on the inclusion of the 'ulem' package in
		# the latex template.
		elementTypes = {
			'bold': {'prefix': '<strong>', 'postfix': '</strong>'},
			'italic': {'prefix': '<em>', 'postfix': '</em>'},
			'underline': {'prefix': '<span style="font-decoration: underline;">', 'postfix': '</span>'},
			'strikethrough': {'prefix': '<span style="font-decoration: line-through;">', 'postfix': '</span>'}
		}

		paragraphText = ''

		for child in paragraphNode.children:

			# Append text element, and if we've encountered an empty paragraph,
			# make sure we insert markup so Latex knows to skip a line.
			if 'text' == child.nodeType:

				if child.value:

					value = child.value

					# Replace special characters with their escaped equivalents
					for char in self.specialChars.keys():
						value = value.replace(char, self.specialChars[char])

					paragraphText += value

				# Empty paragraph
				elif 0 == depth and 1 == len(child.parent.children):
					paragraphText += '&#160;' # &#160; == &nbsp;

			else:

				if child.nodeType in elementTypes.keys():
					paragraphText += elementTypes[child.nodeType]['prefix']
					paragraphText += self.__parseRTFDOMParagraph(child, depth + 1)
					paragraphText += elementTypes[child.nodeType]['postfix']

				elif 'hyperlink' == child.nodeType:
					paragraphText += elementTypes['bold']['prefix']
					paragraphText += self.__parseRTFDOMParagraph(child, depth + 1)
					paragraphText += elementTypes['bold']['postfix']

				elif 'footnote' == child.nodeType:
					paragraphText += child.attributes['text']
					paragraphText += '\\footnote{'
					paragraphText += self.__parseRTFDOMParagraph(child, depth + 1)
					paragraphText += '}'

				# We allow paragraph nodes inside footnotes
				elif 'para' == child.nodeType and 'footnote' == child.parent.nodeType:
					paragraphText += self.__parseRTFDOMParagraph(child, depth + 1)
					paragraphText += '\n\n'

		return paragraphText

	##########################################################################

	# Outputs a file for the part in EPUB format.
	def __transformPart(self, partNode):

		chapterFilename = self.__tmpOutputDir + '/OEBPS/' + str(self.__curChapterIndex).zfill(3) + '_' + re.compile('[^a-zA-Z0-9]').sub('', partNode.value) + '.xhtml'
		outputXHTML  = self._getXHTMLHeader('part', partNode.value, True)
		outputXHTML += self._getXHTMLFooter()

		open(chapterFilename, 'w').write(outputXHTML)

		# Add the part to the table of contents and update self.__curPart so
		# that new chapters, assuming they're inside this part, will be added to
		# it instead of to the root of the table of contents.
		curChapter = {
			'chapter': partNode.value,
			'chapterSlug': self.__invalidIdCharsRegex.sub('', partName),
			'chapterIndex': self.__curChapterIndex,
			'children': []
		}

		self.__curChapterIndex = self.__curChapterIndex + 1
		self.__chapterLog.append(curChapter)
		self.__curTOCPart = curChapter['children']

	##########################################################################

	# Outputs a chapter in EPUB format.
	def __transformChapter(self, chapterNode):

		# Used for part of the chapter's filename
		chapterSlug = self.invalidIdCharsRegex.sub('', chapterNode.value)

		# Add a DIV tag with the chapter's ID
		bodyDivId = 'ch' + self.invalidIdCharsRegex.sub('', chapterNode.value)

		outputXHTML = self._getXHTMLHeader('chapter', chapterNode.value)
		outputXHTML += '\t\t\t<div id="' + bodyDivId + '">\n\n'

		firstParagraph = True
		for paragraph in chapterNode.children:
			if firstParagraph:
				openParagraph = '<p style="text-indent: 0;">'
			else:
				openParagraph = '<p>'
			outputXHTML += '\t\t\t\t' + openParagraph + self.__parseRTFDOMParagraph(paragraph) + '</p>\n'
			firstParagraph = False

		outputXHTML += '\n\t\t\t</div>\n\n'
		outputXHTML += self._getXHTMLFooter()

		chapterFilename = self.__tmpOutputDir + '/OEBPS/' + str(self.__curChapterIndex).zfill(3) + '_' + chapterSlug + '.xhtml'
		open(chapterFilename, 'w').write(outputXHTML)

		self.__curTOCPart.append({
			'chapter': chapterNode.value,
			'chapterSlug': chapterSlug,
			'chapterIndex': self.__curChapterIndex,
			'children': None
		})

		self.__curChapterIndex = self.__curChapterIndex + 1

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, isFiction, coverPath)

		# Generate a unique ID that can be used in /tmp to avoid collisions
		# during concurrently running instances. The Epub driver will also use
		# this for the book's UID.
		self.__uid = str(binascii.hexlify(os.urandom(16))).replace("'", '')[1:]
		self.__tmpOutputDir = tmpLocation + '/' + self.__uid

		# List of chapters processed. Used to create the manifest.
		self.__chapterLog = []

		# Points to the root of the table of contents unless adding a part to
		# the book which will itself contain chapters, and determines where in
		# the TOC a chapter will be listed.
		self.__curTOCPart = self.__chapterLog

		# Used to enumerate chapter files
		self.__curChapterIndex = 1

		# Setup epub template variables
		self.__initTemplateVars()

	##########################################################################

	# Transforms the DOM-like representation of the e-book into the EPUB format.
	def transform(self, DOMRoot, filename):

		# Create the book's directory structure
		try:
			os.mkdir(self.__tmpOutputDir)
			os.mkdir(self.__tmpOutputDir + '/OEBPS')
			os.mkdir(self.__tmpOutputDir + '/META-INF')

		except:
			raise OutputException('Failed to create temporary output directory.')

		# Write out the book's mimetype and meta info
		try:
			mimetypeFile = open(self.__tmpOutputDir + '/mimetype', 'w')
			mimetypeFile.write('application/epub+zip')
			mimetypeFile.close()
			shutil.copyfile(__file__[:-3] + '/templates/container.xml', self.__tmpOutputDir + '/META-INF/container.xml')

		except:
			raise OutputException('Failed to write mimetype.')

		# Output parts and chapters
		for child in DOMRoot.children:

			if 'part' == child.nodeType:

				self.__transformPart(chapterNode)

				for chapter in chapterNode.children:
					self.__transformChapter(chapter)

			else:
				self.__transformChapter(child)

		self.__initChaptersTemplateVars()

		# Write out filled-in templates
		templates = ['style.css', 'book.opf', 'Cover.xhtml', 'toc.ncx', 'title.xhtml', 'toc.xhtml']
		if self._includeCopyright:
			templates.append('copyright.xhtml')

		for templateName in templates:

			try:

				template = self.__hydrate(open(__file__[:-3] + '/templates/' + templateName, 'r').read())

				try:
					open(self.__tmpOutputDir + '/OEBPS/' + templateName, 'w').write(template)
				except:
					raise OutputException('Failed to write ' + templateName + '.')

			except:
				print(__file__[:-3] + '/templates/' + templateName)
				raise OutputException('Failed to read ' + templateName + ' template.')

		# Copy the cover (WARNING: should not exceed 1000 pixels in longest
		# dimension to avoid crashing older e-readers.)
		try:

			# If user specified that they wanted to generate a cover, do so here.
			# This is useful if, say, you want to create an ARC or you want to
			# test the e-book, but no cover has been designed yet.
			if 'generate' == self._coverPath:

				import shlex, subprocess

				# Imagemagick is required to generate a cover, so make sure it exists
				try:
					subprocess.check_output(shlex.split('convert --version'))
				except:
					raise OutputException('Imagemagick must be installed before you can generate a cover.')

				subprocess.check_call(shlex.split('convert -background black -size ' + str(GENERATED_COVER_WIDTH) + 'x' + str(GENERATED_COVER_HEIGHT / 2) + ' -fill "#ffffff" -pointsize 110 -gravity center label:"' + self._bookTitle + '" -pointsize 60 label:"' + self._bookAuthor + '" -append ' + self.__tmpOutputDir + '/OEBPS/Cover.jpg'))

			# The user provided a cover image, so use it
			else:
				# TODO: actually do extensive validation of the image before just
				# blindly copying it over ;)
				shutil.copyfile(self._coverPath, self.__tmpOutputDir + '/OEBPS/Cover.jpg')

		except Exception as e:

			raise OutputException('Could not copy or generate cover: ' + str(e))

		# Finally, write the ePub file. Phew!
		self.__zipBook(filename)

	##########################################################################

	# Cleans up the mess left behind after an e-book conversion.
	def cleanup(self):

		try:
			shutil.rmtree(self.__tmpOutputDir)

		# If this is on the backend of a server, I don't want people to get
		# error messages about it. But /tmp should be monitored to make sure
		# it's not filling up because this is silently failing.
		except:
			pass

