# -*- coding: utf-8 -*-

import re, os, zipfile, shutil
import util

from pyrtfdom.dom import RTFDOM
from pyrtfdom import elements

from exception import InputException
from .driver import Driver
from ..domnode import EbookNode

class Rtf(Driver):

	# Utility method to extract all text from a paragraph node unformatted.
	def __extractParagraphText(self, paragraphNode):

		paragraphText = ''
		formatElementTypes = ['bold', 'italic', 'underline', 'strikethrough']

		for child in paragraphNode.children:

			# Append text element
			if 'text' == child.nodeType:

				if child.value:
					paragraphText += child.value

				else:
					paragraphText += ' '

			else:

				if child.nodeType in formatElementTypes():
					paragraphText += self.__parseRTFDOMParagraph(child)

		return paragraphText

	##########################################################################

	# Constructor
	def __init__(self):

		super().__init__()

		# Initialize the RTF parser
		self.__domTree = RTFDOM()

	##########################################################################

	def open(self, filename):

		super().open(filename)

		# super().open() only checks if the path exists, because some input
		# drivers (not this one) support directories as well as files.
		if not os.path.isfile(self._inputPath):
			raise InputException('Input path ' + self._inputPath + ' must be a file.')

	##########################################################################

	def parse(self):

		self.__domTree.openFile(self._inputPath)
		self.__domTree.parse()

		curChapterNode = None
		firstParagraph = True

		for child in self.__domTree.rootNode.children:

			if firstParagraph or (
				'pagebreakBefore' in child.attributes and
				child.attributes['pagebreakBefore']
			):
				chapterTitle = self.__extractParagraphText(child)
				print('Processing Chapter "' + chapterTitle + '"...')
				curChapterNode = EbookNode('chapter')
				curChapterNode.value = chapterTitle
				self._curDOMNode.appendChild(curChapterNode)
				firstParagraph = False

			else:
				curChapterNode.appendChild(child)
