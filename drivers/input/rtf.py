# -*- coding: utf-8 -*-

import re, os, zipfile, shutil
import util, driver

from pyrtfdom.dom import RTFDOM
from pyrtfdom import elements

class Rtf(driver.Driver):

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
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation)

		# Initialize the RTF parser
		self.domTree = RTFDOM()

	##########################################################################

	# Nothing really special required to open an RTF, so just implement this for
	# the sake of filling in an abstract method. 
	def openDriver(self):
		pass

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

	# Processes a Scrivener HTML-exported chapter, transforming it into
	# ePub friendly XHTML.
	def transformChapter(self, inputText):

		# HACK: we store the title and RTF text in the same string for legacy
		# purposes, so split them up real quick before continuing.
		chapterHeading = inputText[0:inputText.find('\n')]
		inputText = inputText[inputText.find('\n') + 1:]

		# Add a DIV tag with the chapter's ID
		bodyDivId = 'ch' + self.invalidIdCharsRegex.sub('', chapterHeading)

		# Parse the RTF into a DOM-like structure
		self.domTree.openString(inputText)
		self.domTree.parse()

		outputXHTML = self._getXHTMLHeader('chapter', chapterHeading)
		outputXHTML += '\t\t\t<div id="' + bodyDivId + '">\n\n'

		firstParagraph = True
		for paragraph in self.domTree.rootNode.children:
			if firstParagraph:
				openParagraph = '<p style="text-indent: 0;">'
			else:
				openParagraph = '<p>'
			outputXHTML += '\t\t\t\t' + openParagraph + self.__parseRTFDOMParagraph(paragraph) + '</p>\n'
			firstParagraph = False

		outputXHTML += '\n\t\t\t</div>\n\n'
		outputXHTML += self._getXHTMLFooter()

		return {
			'chapter': chapterHeading,
			'chapterSlug': self.invalidIdCharsRegex.sub('', chapterHeading),
			'chapterIndex': self.curChapterIndex,
			'text': outputXHTML
		}

	##########################################################################

	# Iterates through a Scrivener project and runs processChapter on each
	# contained chapter. Recursively enters project folders. The first folder,
	# if it exists, will be treated as a part, a subdivision above chapter.
	def processChapters(self, inputPath, parentNode = False, depth = 0):

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
					self.processChapters(inputPath, binderItem.find('Children'), depth)
					return

		for binderItem in parentNode:

			chapterTitle = binderItem.find('Title').text

			# Make sure root chapters always show up in the root of the table of
			# contents. Without this line of code, if there's a previously
			# processed part, the chapter will be added to it even if the chapter
			# is supposed to be outside of it.
			if 0 == depth and ('Text' == binderItem.attrib['Type'] or 'Folder' == binderItem.attrib['Type']):
				self.closeCurrentPart()

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
					self.processPart(chapterTitle)
				self.processChapters(inputPath, binderItem.find('Children'), depth + 1)

