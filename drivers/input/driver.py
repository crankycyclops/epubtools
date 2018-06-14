# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod
from ..domnode import EbookNode

# Input driver base class
class Driver:

	__metaclass__ = ABCMeta

	##########################################################################

	# Constructor
	def __init__(self):

		# We use a DOM-like structure to represent the contents of an ebook.
		# Parts and chapters are all children of this node.
		self.DOMRoot = EbookNode('ebook')

		# Represents our current location in the ebook's "DOM" while parsing.
		self._curDOMNode = self.DOMRoot

	##########################################################################

	# Opens the input source for reading and throws an exception if opening
	# the document failed. If a driver needs to do more than what this method
	# does, then it should override this function and call super().open().
	def open(self, filename):

		self._inputPath = filename

	##########################################################################

	# Parse the input document into a DOM-like representation and return it,
	# along with the contents of self.chapterLog, so that the output driver can
	# work its black voodoo magic.
	# TODO: detail the DOM structure in more detail
	@abstractmethod
	def parse(self):

		pass

	##########################################################################

	# Cleans up after parsing is complete. If there's no cleanup to do for a
	# particular driver, just implement an empty function.
	@abstractmethod
	def cleanup(self):

		pass

	###########################################################################

	# A debug method that allows me to see what the parsed DOM looks like.
	def printTree(self, curNode = None, indent = ''):

		if curNode is None:
			curNode = self.DOMRoot

		nodeAttributes = '{'
		for key in curNode.attributes.keys():
			nodeAttributes += "'" + key + "': " + str(curNode.attributes[key]) + ", "
		if len(nodeAttributes) > 1:
			nodeAttributes = nodeAttributes[0:len(nodeAttributes) - 2]
		nodeAttributes += '}'

		if isinstance(curNode.value, (bytes, bytearray)):
			nodeValue = '<Binary Data>'
		else:
			nodeValue = curNode.value

		print('')
		print(indent + 'nodeType: ' + curNode.nodeType)
		print(indent + 'attributes: ' + nodeAttributes)
		print(indent + 'value: ' + nodeValue)
		print(indent + 'children: ' + str(curNode.childCount()))

		if curNode.children:
			for child in curNode.children:
				self.printTree(child, indent + '\t')

