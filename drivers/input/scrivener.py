# -*- coding: utf-8 -*-

import os, zipfile, shutil, binascii
import xml.etree.ElementTree as ET

from pyrtfdom.dom import RTFDOM
from pyrtfdom import elements

from exception import InputException
from .driver import Driver
from ..domnode import EbookNode

import util

class Scrivener(Driver):

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
					raise InputException('Failed to parse ' + self._curChapterFilenamePrefix + '.comments')

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

		self.__domTree.registerFieldDriver('HYPERLINK', scrivHyperlinkDriver)

	##########################################################################

	# Opens up a ZIP file for input and passes back the path to the extracted
	# contents.
	def __openZipInput(self, filename):

		try:

			os.mkdir(self.extractPath)
			archive = zipfile.ZipFile(filename)

			# This should be safe as of Python 2.7.4, which adds path
			# traversal protection
			archive.extractall(self.extractPath)
			return self.extractPath

		except OSError:
			raise InputException('Error occurred during input ZIP extraction. This is a bug.')

		except zipfile.BadZipfile:
			raise InputException('Input ZIP file is invalid.')

		except:
			raise InputException('Could not extract input ZIP file.')

	##########################################################################

	# Uses RTFDOM to parse an individual chapter and adds it to the ebook's DOM.
	def __parseChapter(self, chapterTitle, filename):

		chapterNode = EbookNode('chapter')
		chapterNode.value = chapterTitle

		self.__domTree.openFile(filename)
		self.__domTree.parse()

		for child in self.__domTree.rootNode.children:
			chapterNode.appendChild(child)

		self._curDOMNode.appendChild(chapterNode)

	##########################################################################

	# Constructor
	def __init__(self, tmpLocation = '/tmp'):

		super().__init__()

		# Initialize the RTF parser
		self.__domTree = RTFDOM()
		self.__registerCustomFieldDrivers()

		# Generate a unique ID that can be used in /tmp to avoid collisions
		# during concurrently running instances.
		self.__uid = str(binascii.hexlify(os.urandom(16))).replace("'", '')[1:]
		self.__tmpOutputDir = tmpLocation + '/' + self.__uid

		# Where we extract ZIP archives, if a ZIP archive was passed as input
		self.__extractPath = self.__tmpOutputDir + '_input'

	##########################################################################

	def open(self, filename):

		super().open(filename)

		# Add support for ZIP archives
		if '.zip' == self._inputPath[-4:].lower():
			self._inputPath = self.__openZipInput(self._inputPath)

	##########################################################################

	# Iterates through a Scrivener project and parses each contained chapter.
	# Recursively enters project folders. The first folder, if it exists, will
	# be treated as a "part," a subdivision above chapter.
	def parse(self, parentNode = False, depth = 0):

		if not parentNode:

			scrivxPath = False

			for filename in os.listdir(self._inputPath):
				if filename.endswith('.scrivx'):
					scrivxPath = os.path.join(self._inputPath, filename)
					break

			if not scrivxPath:
				raise InputException(self._inputPath + ' is not a valid Scrivener project.')

			try:
				tree = ET.parse(scrivxPath)
			except:
				raise InputException('Failed to open ' + scrivxPath + ' for parsing.')

			parentNode = tree.getroot()

			if parentNode.tag != 'ScrivenerProject':
				raise InputException(self._inputPath + ' is not a valid Scrivener project.')

			# We only want to process files found in the Draft Folder. Notes and
			# other things in other zero depth folders should be ignored.
			for binderItem in parentNode.find('Binder').findall('BinderItem'):
				if 'DraftFolder' == binderItem.attrib['Type']:
					self.parse(binderItem.find('Children'), depth)
					return

		for binderItem in parentNode:

			chapterTitle = binderItem.find('Title').text

			# Make sure root chapters always show up in the root of the table of
			# contents. Without this line of code, if there's a previously
			# processed part, the chapter will be added to it even if the chapter
			# is supposed to be outside of it.
			if 0 == depth and ('Text' == binderItem.attrib['Type'] or 'Folder' == binderItem.attrib['Type']):
				self._curDOMNode = self.DOMRoot

			# Chapter
			if 'Text' == binderItem.attrib['Type']:

				print('Processing Chapter "' + chapterTitle + '"...')

				self._curChapterFilenamePrefix = self._inputPath + '/Files/Docs/' + binderItem.attrib['ID']
				self.__parseChapter(chapterTitle, self._curChapterFilenamePrefix  + '.rtf')

			elif 'Folder' == binderItem.attrib['Type']:

				# We've encountered a titled part of the book containing chapters
				if 0 == depth:

					print('Processing Part "' + chapterTitle + '"...')

					partNode = EbookNode('part')
					partNode.value = chapterTitle
					self._curDOMNode.appendChild(partNode)
					self._curDOMNode = partNode

				self.parse(self._inputPath, binderItem.find('Children'), depth + 1)

	##########################################################################

	# If we extracted a ZIP archive, we need to delete those temporary files.
	def cleanup(self):

		try:
			if os.path.exists(self.__extractPath):
				shutil.rmtree(self.__extractPath)

		# If for some reason we can't remove these files, I don't want a backend
		# process on a server to return with an error. So we'll just silently
		# fail and monitor /tmp from time to time to make sure it doesn't fill
		# up with too many files.
		except:
			pass

