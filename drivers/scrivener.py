# -*- coding: utf-8 -*-

import re, os, zipfile, shutil
import xml.etree.ElementTree as ET
import util, driver

from pyrtfdom.dom import RTFDOM
from pyrtfdom import elements

class Scrivener(driver.Driver):

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

	# Scrivener footnotes are implemented internally as a special type of
	# hyperlink field, so I need to override this field type (and possibly
	# others in the future.)
	def __registerCustomFieldDrivers(self):

		# Override the hyperlink driver, since Scrivener projects use hyperlinks
		# internally for comments and footnotes.
		def scrivHyperlinkDriver(dom, fldPara, fldrslt):

			curParNode = dom.curNode.parent
			href = fldPara[1:len(fldPara) - 1]

			# We have just a plain hyperlink, so pass through to the original
			# field driver.
			if ('scrivcmt://' != href[0:11]):
				dom.runDefaultFieldDriver('HYPERLINK', fldPara, fldrslt)

			# We have a Scrivener-specific hyperlink, which means we've
			# encountered either a comment or a footnote and have to do some
			# extra custom logic to parse it out.
			else:

				# First, parse the comments XML file associated with the chapter
				# we're currently processing.
				try:
					commentsXML = ET.parse(self._curChapterFilenamePrefix + '.comments')
				except:
					raise Exception('Failed to parse ' + self._curChapterFilenamePrefix + '.comments')

				comments = commentsXML.findall("./Comment[@ID='" + href[11:] + "']")

				# Comment element couldn't be found, or it's not a footnote, so
				# instead, append the text without the footnote.
				if (
					not comments or
					not comments[0].get('Footnote') or
					'Yes' != comments[0].get('Footnote')
				):
					dom.insertFldrslt(fldrslt)

				# The footnote exists, so go ahead and append it to the DOM.
				else:

					subTree = RTFDOM()
					subTree.openString(comments[0].text)
					subTree.parse()

					curParNode = dom.curNode.parent

					# If the previous text element was empty, it's unnecessary and can
					# be removed to simplify the tree.
					if 0 == len(dom.curNode.value):
						dom.removeCurNode()

					# Footnote is the only element other than RTFElement that
					# accepts paragraphs as child nodes.
					footnoteNode = elements.FootnoteElement()
					footnoteNode.attributes['text'] = self.__parseRTFDOMParagraph(RTFDOM.parseSubRTF('{' + fldrslt + '}').children[0])
					for paraNode in subTree.rootNode.children:
						footnoteNode.appendChild(paraNode)

					curParNode.appendChild(footnoteNode)

					# Insert a new empty text element into the current paragraph
					# after the footnote so we can continue appending new text.
					dom.initTextElement(curParNode)

		#####

		self.domTree.registerFieldDriver('HYPERLINK', scrivHyperlinkDriver)

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation)

		# Where we extract ZIP archives, if a ZIP archive was passed as input
		self.extractPath = self.tmpOutputDir + '_input'

		# Initialize the RTF parser
		self.domTree = RTFDOM()
		self.__registerCustomFieldDrivers()

	##########################################################################

	# Opens up a ZIP file for input and passes back the path to the extracted
	# contents.
	def openZipInput(self, inputFilename):

		try:

			os.mkdir(self.extractPath)
			archive = zipfile.ZipFile(inputFilename)

			# This should be safe as of Python 2.7.4, which adds path
			# traversal protection
			archive.extractall(self.extractPath)
			return self.extractPath

		except OSError:
			raise Exception('Error occurred during extraction. This is a bug.')

		except zipfile.BadZipfile:
			raise Exception('ZIP file is invalid.')

		except:
			raise Exception('Could not extract ZIP file.')

	##########################################################################

	def openDriver(self):

		# Support for ZIP archives
		if '.zip' == self.inputPath[-4:].lower():
			self.inputPath = self.openZipInput(self.inputPath)

	##########################################################################

	def cleanup(self):

		try:
			if os.path.exists(self.extractPath):
				shutil.rmtree(self.extractPath)
			super().cleanup()

		# We should at least still try to let the base class run its cleanup.
		except:
			super().cleanup()

	##########################################################################

	# Utility function to recursively parse an RTFDOM paragraph node into Latex.
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
					paragraphText += '&nbsp;'

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

	# Processes a Scrivener HTML-exported chapter, transforming it into
	# ePub friendly XHTML.
	def transformChapter(self, inputText):

		# HACK: we store the title and RTF text in the same string for legacy
		# purposes, so split them up real quick before continuing.
		chapterHeading = inputText[0:inputText.find('\n')]
		inputText = inputText[inputText.find('\n') + 1:]

		# Add a DIV tag with the chapter's ID
		invalidIdCharsRegex = re.compile('[^a-zA-Z0-9]')
		bodyDivId = 'ch' + invalidIdCharsRegex.sub('', chapterHeading)

		# Parse the RTF into a DOM-like structure
		self.domTree.openString(inputText)
		self.domTree.parse()

		# TODO: should xml:lang be set to whichever language the e-book is in,
		# and if so, how do I map that value?
		outputXHTML  = '<?xml version="1.0" encoding="UTF-8"?>\n'
		outputXHTML += '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" xmlns:epub="http://www.idpf.org/2007/ops">\n\n'

		outputXHTML += '\t<head>\n'
		outputXHTML += '\t\t<meta charset="utf-8" />\n'
		outputXHTML += '\t\t<title>' + self.bookTitle + '</title>\n'
		outputXHTML += '\t\t<link rel="stylesheet" href="style.css" type="text/css" />\n'
		outputXHTML += '\t</head>\n\n'

		outputXHTML += '\t<body>\n\n'
		outputXHTML += '\t\t<section epub:type="bodymatter chapter">\n\n'

		outputXHTML += '\t\t\t<header>\n'
		outputXHTML += '\t\t\t\t<h1>' + chapterHeading + '</h1>\n'
		outputXHTML += '\t\t\t</header>\n\n'

		outputXHTML += '\t\t\t<div id="' + bodyDivId + '">\n\n'

		for paragraph in self.domTree.rootNode.children:
			outputXHTML += '\t\t\t\t<p>' + self.__parseRTFDOMParagraph(paragraph) + '</p>\n'

		outputXHTML += '\n\t\t\t</div>\n\n'
		outputXHTML += '\t\t</section>\n\n'
		outputXHTML += '\t</body>\n\n'
		outputXHTML += '</html>'

		return {
			'chapter': chapterHeading,
			'chapterSlug': invalidIdCharsRegex.sub('', chapterHeading),
			'text': outputXHTML
		}

	##########################################################################

	# Iterates through a Scrivener project and runs processChapter on each
	# contained chapter. Recursively enters project folders. The first folder,
	# if it exists, will be treated as a part, a subdivision above chapter.
	def processChaptersList(self, inputPath, parentNode = False, depth = 0):

		if not parentNode:

			scrivxPath = False

			for filename in os.listdir(inputPath):
				if filename.endswith('.scrivx'):
					scrivxPath = os.path.join(inputPath, filename)
					break

			if not scrivxPath:
				raise Exception(inputPath + ' is not a valid Scrivener project.')

			try:
				tree = ET.parse(scrivxPath)
			except:
				raise Exception('Failed to open ' + scrivxPath + ' for parsing.')

			parentNode = tree.getroot()

			if parentNode.tag != 'ScrivenerProject':
				raise Exception(inputPath + ' is not a valid Scrivener project.')

			# We only want to process files found in the Draft Folder. Notes and
			# other things in other zero depth folders should be ignored.
			for binderItem in parentNode.find('Binder').findall('BinderItem'):
				if 'DraftFolder' == binderItem.attrib['Type']:
					self.processChaptersList(inputPath, binderItem.find('Children'), depth)
					return

		for binderItem in parentNode:

			chapterTitle = binderItem.find('Title').text

			# Chapter
			if 'Text' == binderItem.attrib['Type']:

				print('Processing Chapter "' + chapterTitle + '"...')

				self._curChapterFilenamePrefix = inputPath + '/Files/Docs/' + binderItem.attrib['ID']

				rtfFile = open(self._curChapterFilenamePrefix  + '.rtf')
				rtfStr = rtfFile.read()
				rtfFile.close()

				# HACK: place the chapter title at the top of the RTF string.
				# processChapter() will know what to do with it.
				rtfStr = chapterTitle + '\n' + rtfStr
				self.processChapter(rtfStr)

			# A titled part of the book containing chapters
			elif 'Folder' == binderItem.attrib['Type']:
				if 0 == depth:
					print('Processing Part "' + chapterTitle + '"...')
					#self.processPart(chapterTitle): TODO: implement support for parts
				self.processChaptersList(inputPath, binderItem.find('Children'), depth + 1)

