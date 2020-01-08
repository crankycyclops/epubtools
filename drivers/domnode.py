# -*- coding: utf-8 -*-

from pyrtfdom import elements

# I'm using a DOM-like structure to represent the contents of an e-book
# internally. Since I'm already making heavy use of my PyRTFDOM library and
# already have all that code written, I'm just going to extend its DOMElement
# class so I can define a couple extra types and also maintain compatibility
# with the data I parse using PyRTFDOM.
class EbookNode(elements.DOMElement):

	def __init__(self, nodeType):

		super().__init__(nodeType)
