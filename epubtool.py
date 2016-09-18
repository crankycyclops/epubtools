#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import util
import drivers.scrivener

###############################################################################

# Using print as a function requires Python 3
if len(sys.argv) < 10 or len(sys.argv) > 11:
	util.eprint("\nUsage: " + sys.argv[0] + " <input source: zip or dir> <output epub file> <book title> <author> <copyright year> <0 = no copyright page, 1 = include copyright page> <lang> <publication date: YYYY-MM-DD> <path to cover image> [publisher name (author name used if blank)]\n")
	sys.exit(1)

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]
title = sys.argv[3]
author = sys.argv[4]
copyrightYear = sys.argv[5]

if '1' == sys.argv[6]:
	includeCopyright = True
else:
	includeCopyright = False

lang = sys.argv[7] # Example: "en-US"
pubDate = sys.argv[8] #Valid value: YYYY-MM-DD
coverPath = sys.argv[9]

if 10 == len(sys.argv):
	publisher = sys.argv[9]
else:
	publisher = author

# TODO: for now, we're just assuming Scrivener html export input format
try:
	driver = drivers.Scrivener(lang, publisher, author, title, pubDate,
		copyrightYear, includeCopyright, coverPath)
except Exception as error:
	util.eprint('\n' + error.args[0] + '\n')
	sys.exit(1)

try:
	driver.openInput(inputFilename)
	driver.processBook(outputFilename)
	driver.cleanup()
	sys.exit(0)

except Exception as error:
	driver.cleanup()
	util.eprint('\n' + error.args[0] + '\n')
	sys.exit(1)

