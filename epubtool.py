#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, argparse
import util

import drivers.input
import drivers.output
from process import Process

###############################################################################

# Python's argparse is spiffy. Seriously.
parser = argparse.ArgumentParser(description='Convert a document into an e-book.')

parser.add_argument(
	'-I',
	dest='INPUT_DRIVER',
	nargs=1,
	required=True,
	help='Driver that knows how to read your input document (required)'
)

parser.add_argument(
	'-O',
	dest='OUTPUT_DRIVER',
	nargs=1,
	default=['epub'],
	help='Default: epub'
)

parser.add_argument(
	'--title',
	dest='TITLE',
	nargs=1,
	required=True,
	help='Title of the book (required)'
)

parser.add_argument(
	'--author',
	dest='AUTHOR',
	nargs=1,
	required=True,
	help='Author of the book (required)'
)

parser.add_argument(
	'--publisher',
	dest='PUBNAME',
	nargs=1,
	help='Publisher of the book (if not set, the author name will be used)'
)

parser.add_argument(
	'--lang',
	dest='LANGUAGE',
	nargs=1,
	required=True,
	help='Language of the book (required, ex: en-US)'
)

parser.add_argument(
	'--copyrightYear',
	dest='YEAR',
	type=int,
	nargs=1,
	required=True,
	help='Copyright year in YYYY format (required)'
)

parser.add_argument(
	'--pubDate',
	dest='DATE',
	nargs=1,
	required=True,
	help='Publication date in YYYY-MM-DD format (required)'
)

parser.add_argument(
	'--coverPath',
	dest='COVER',
	nargs=1,
	required=True,
	help='Path to cover image (required, "generate" = generate a test cover)'
)

# TODO: selecting this currently doesn't work; it just always uses the default
parser.add_argument(
	'--includeCopyright',
	action='store_true',
	default=True,
	help='Include copyright page (default)'
)

# TODO: selecting this currently doesn't work; it just always uses the default
parser.add_argument(
	'--isFiction',
	action='store_true',
	default=True,
	help='Book is a work of fiction (default)'
)

parser.add_argument(
	'INPUT',
	help='Document input file (required)'
)

parser.add_argument(
	'OUTPUT',
	help='E-book output file (required)'
)

args = parser.parse_args()

# If no publisher name is set, default to the author's name instead
if None == args.PUBNAME:
	args.PUBNAME = args.AUTHOR

###############################################################################

# Attempt to load the specified input and output drivers and fail if any of the
# corresponding classes don't exist.
try:

	InputDriverClass = getattr(drivers.input, args.INPUT_DRIVER[0].lower().capitalize())
	inputDriver = InputDriverClass()

# TODO: if exception thrown from within class, we need to catch that and report its
# error instead.
except Exception as error:

	util.eprint('\nDriver ' + args.INPUT_DRIVER[0].lower().capitalize() + ' is not supported.\n')
	sys.exit(3)

#try:

OutputDriverClass = getattr(drivers.output, args.OUTPUT_DRIVER[0].lower().capitalize())
outputDriver = OutputDriverClass(args.LANGUAGE[0], args.PUBNAME[0], args.AUTHOR[0],
		args.TITLE[0], args.DATE[0], str(args.YEAR[0]), args.includeCopyright,
		args.isFiction, args.COVER[0])

# TODO: if exception thrown from within class, we need to catch that and report its
# error instead. Can catch a specific kind of error, then any other errors
# just get passed through.
#except Exception as error:

#	util.eprint('\nDriver ' + args.OUTPUT_DRIVER[0].lower().capitalize() + ' is not supported.\n')
#	sys.exit(3)

###############################################################################

# Create the e-book :)
try:

	process = Process(inputDriver, outputDriver)

	process.open(args.INPUT)
	process.convert(args.OUTPUT)
	process.cleanup()

	sys.exit(0)

#	inputDriver.openInput(args.INPUT)
#	inputDriver.processBook(args.OUTPUT)
#	inputDriver.cleanup()
#	sys.exit(0)

# Boo!
except Exception as error:

	import traceback
	util.eprint('\nTraceback:\n')
	traceback.print_tb(error.__traceback__)
	util.eprint('\nError: ' + error.args[0] + '\n')

	driver.cleanup()
	sys.exit(4)

