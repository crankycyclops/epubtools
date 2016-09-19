#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import util
import drivers.scrivener

###############################################################################

# Using print as a function requires Python 3
if len(sys.argv) < 11 or len(sys.argv) > 12:
	util.eprint("\nUsage: " + sys.argv[0] + " <input driver: doc | scriv> <input source: zip or dir> <output epub file> <book title> <author> <copyright year> <0 = no copyright page, 1 = include copyright page> <lang> <publication date: YYYY-MM-DD> <path to cover image> [publisher name (author name used if blank)]\n")
	sys.exit(1)

inputDriver = sys.argv[1].lower()
inputFilename = sys.argv[2]
outputFilename = sys.argv[3]
title = sys.argv[4]
author = sys.argv[5]
copyrightYear = sys.argv[6]

if '1' == sys.argv[7]:
	includeCopyright = True
else:
	includeCopyright = False

lang = sys.argv[8] # Example: "en-US"
pubDate = sys.argv[9] #Valid value: YYYY-MM-DD
coverPath = sys.argv[10]

if 12 == len(sys.argv):
	publisher = sys.argv[11]
else:
	publisher = author

try:

	if 'scriv' == inputDriver:
		driver = drivers.Scrivener(lang, publisher, author, title, pubDate,
			copyrightYear, includeCopyright, coverPath)

	elif 'doc' == inputDriver:
		# TODO
		util.eprint('\ndoc driver not yet implemented.\n')
		sys.exit(1)

	else:
		util.eprint('\n' + inputDriver + 'driver not supported.\n')
		sys.exit(2)

except Exception as error:
	util.eprint('\n' + error.args[0] + '\n')
	sys.exit(3)

try:
	driver.openInput(inputFilename)
	driver.processBook(outputFilename)
	driver.cleanup()
	sys.exit(0)

except Exception as error:
	driver.cleanup()
	util.eprint('\n' + error.args[0] + '\n')
	sys.exit(4)

