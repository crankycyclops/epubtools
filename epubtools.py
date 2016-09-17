#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import util, drivers.scrivener

###############################################################################

# Using print as a function requires Python 3
if len(sys.argv) < 3 or len(sys.argv) > 5:
	util.eprint("\nUsage: " + sys.argv[0] + " <input file> <output file> [book title]\n")
	sys.exit(1)

inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

bookTitle = ''
if 4 == len(sys.argv):
	bookTitle = sys.argv[3]

try:
	inputFile = open(inputFilename, 'r')
	inputText = inputFile.read()

except:
	util.eprint("\nCould not open " + inputFilename + " for reading.\n")
	sys.exit(2)

driver = drivers.scrivener.HTML(bookTitle)
inputText = driver.transform(inputText)

try:
	outputFile = open(outputFilename, 'w')
	outputFile.write(inputText)

except:
	util.eprint("\nFailed to write output to " + outputFilename)
	sys.exit(3)

