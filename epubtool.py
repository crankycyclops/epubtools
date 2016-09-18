#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import util
import drivers.scrivener

###############################################################################

# Using print as a function requires Python 3
if len(sys.argv) < 7 or len(sys.argv) > 8:
	util.eprint("\nUsage: " + sys.argv[0] + " <input source: zip or dir> <output epub file> <book title> <author> <copyright year> <0 = no copyright page, 1 = include copyright page> [publisher name (author name used if blank)]\n")
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

if 8 == len(sys.argv):
	publisher = sys.argv[7]
else:
	publisher = author

# TODO: for now, we're just assuming Scrivener html export input format
driver = drivers.Scrivener(publisher, author, title, copyrightYear, includeCopyright)

try:
	driver.openInput(inputFilename)
	driver.processBook(outputFilename)
	driver.cleanup()

except Exception as error:
	driver.cleanup()
	util.eprint('\n' + error.args[0] + '\n')

