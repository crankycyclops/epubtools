#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import util
import drivers.scrivener

###############################################################################

# Using print as a function requires Python 3
if len(sys.argv) != 6:
	util.eprint("\nUsage: " + sys.argv[0] + " <book title> <author> <copyright year> <input source: zip or dir> <output epub file>\n")
	sys.exit(1)

bookTitle = sys.argv[1]
bookAuthor = sys.argv[2]
copyrightYear = sys.argv[3]
inputFilename = sys.argv[4]
outputFilename = sys.argv[5]

# TODO: for now, we're just assuming Scrivener html export input format
driver = drivers.Scrivener(bookAuthor, bookTitle, copyrightYear)

try:
	driver.openInput(inputFilename)
	driver.processBook(outputFilename)
	driver.cleanup()

except Exception as error:
	util.eprint('\n' + error.args[0] + '\n')

