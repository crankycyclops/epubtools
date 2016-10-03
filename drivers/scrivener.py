# -*- coding: utf-8 -*-

import re, os, zipfile, shutil
import util, driver

class Scrivener(driver.Driver):

	specialChars = {
		"’": "&#8217;", #rsquo
		"‘": "&#8216;", #lsquo
		"”": "&#8221;", #rdquo
		"“": "&#8220;", #ldquo
		"…": "&#8230;", #hellip
		"—": "&#8212;", #mdash
		"–": "&#8211;", #ndash
		"™": "&#8482;", #trade
		"©": "&#169;",  #copy
		"®": "&#174;"   #reg
	}

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation)

		# Where we extract ZIP archives, if a ZIP archive was passed as input
		self.extractPath = self.tmpOutputDir + '_input'

	##########################################################################

	# Opens up a ZIP file for input and passes back the path to the extracted
	# contents.
	def openZipInput(self, inputFilename):

		try:

			os.mkdir(self.extractPath)
			archive = zipfile.ZipFile(inputFilename)

			# This should be safe as of Python 2.7.4, which adds path
			# traversal protection
			archive.extractall(self.extractPath)
			return self.extractPath

		except OSError:
			raise Exception('Error occurred during extraction. This is a bug.')

		except zipfile.BadZipfile:
			raise Exception('ZIP file is invalid.')

		except:
			raise Exception('Could not extract ZIP file.')

	##########################################################################

	def openDriver(self):

		# Support for ZIP archives
		if '.zip' == self.inputPath[-4:].lower():
			self.inputPath = self.openZipInput(self.inputPath)

		try:
			self.chaptersList = util.natural_sort(os.listdir(self.inputPath))

		except:
			raise Exception("An error occurred while trying to open '" + self.inputPath + ".'")

	##########################################################################

	def cleanup(self):

		try:
			if os.path.exists(self.extractPath):
				shutil.rmtree(self.extractPath)
			super().cleanup()

		# We should at least still try to let the base class run its cleanup.
		except:
			super().cleanup()

	##########################################################################

	# Processes a Scrivener HTML-exported chapter, transforming it into
	# ePub friendly XHTML.
	def transformChapter(self, inputText):

		# Replace doctype
		inputText = inputText.replace(
			'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">',
			'<?xml version="1.0" encoding="UTF-8"?>'
		)

		# Add extra necessary magic to html tag
		inputText = inputText.replace(
			'<html>',
			'<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en" xmlns:epub="http://www.idpf.org/2007/ops">\n\n'
		)

		# Clean up charset meta tag
		inputText = inputText.replace('<meta http-equiv="Content-Type" content="text/html;', '<meta')
		inputText = inputText.replace('charset=utf-8"', 'charset="utf-8"')

		# Strip out unnecessary meta tags
		inputText = inputText.replace('<meta name="qrichtext" content="1" />', '')

		# Strip out unnecessary style tags
		styleTagRegex = re.compile('(?s)<style(.*?)<\/style>')
		inputText = styleTagRegex.sub('', inputText)

		# Cleanup body tags and add extra whitespace to set things off more nicely
		bodyTagRegex = re.compile('<body.*?>')
		inputText = bodyTagRegex.sub('<body>\n', inputText)
		inputText = inputText.replace('</body>', '\n\n</body>\n\n')

		# Cleanup p tags
		pTagRegex = re.compile('<p.*?>')
		inputText = pTagRegex.sub('<p>', inputText)

		# Replace special typographical characters with XHTML-compliant entities
		for char in self.specialChars.keys():
			inputText = inputText.replace(char, self.specialChars[char])

		# Add whitespace to make head and meta tags more readable
		inputText = inputText.replace("<head>", "\t<head>\n")
		inputText = inputText.replace("</head>", "\t</head>\n\n")

		metaTagRegex = re.compile('(<meta.*?>)')
		inputText = metaTagRegex.sub(r'\t\t\1\n', inputText)

		# Fix Title tag (and extract chapter heading for later insertion in the body)
		titleTagRegex = re.compile('(<title>(.*?)</title>)')
		chapterHeading = titleTagRegex.search(inputText).group(2)
		inputText = titleTagRegex.sub('\t\t<title>' + self.bookTitle + '</title>', inputText)

		# Add a generic stylesheet, which will have to be provided externally
		inputText = inputText.replace(
			'</title>',
			'</title>\n\t\t<link rel="stylesheet" href="style.css" type="text/css" />\n'
		)

		# Add section to body, along with a header for the title, and add proper whitespace
		invalidIdCharsRegex = re.compile('[^a-zA-Z0-9]')
		bodyDivId = 'ch' + invalidIdCharsRegex.sub('', chapterHeading)

		bodyRegex = re.compile('(?s)(<body>)(.*?)(<\/body>)')
		inputText = bodyRegex.sub(
			'\t' + r'\1' + '\n\n\t\t<section epub:type="bodymatter chapter">' +
				'\n\n\t\t\t<header>\n\t\t\t\t<h1>' + chapterHeading + '</h1>\n' +
				'\t\t\t</header>\n\n\t\t\t<div id="' + bodyDivId + '">' +
				r'\2' + '\t\t\t</div>\n\n\t\t</section>\n\n' + '\t' + r'\3'
		, inputText)
		inputText = inputText.replace('<p>', '\t\t\t\t<p>')

		# Finally, replace span tags with appropriate em and strong tags
		spanTagRegex = re.compile('((<span(.+?)>)(.*?)(</span>))')

		spanTagMatch = spanTagRegex.search(inputText)
		while spanTagMatch:

			openingTags = ''
			closingTags = ''

			if 'italic' in spanTagMatch.group(2):
				openingTags = '<em>' + openingTags
				closingTags = closingTags + '</em>'

			if 'font-weight' in spanTagMatch.group(2):
				openingTags = '<strong>' + openingTags
				closingTags = closingTags + '</strong>'

			# replacing with [span and later doing a string replace to fix it
			# prevents infinite loops when we keep detecting inserted span
			# tags for underlines
			if 'underline' in spanTagMatch.group(2):
				openingTags = '[span style="font-decoration: underline;">' + openingTags
				closingTags = closingTags + '</span>'

			replacement = openingTags + spanTagMatch.group(4) + closingTags
			inputText = inputText.replace(spanTagMatch.group(1), replacement)

			spanTagMatch = spanTagRegex.search(inputText)

		# See comment about [span inside spanTagMatch while loop
		inputText = inputText.replace('[span', '<span')

		return {
			'chapter': chapterHeading,
			'chapterSlug': invalidIdCharsRegex.sub('', chapterHeading),
			'text': inputText
		}

	##########################################################################

	# Iterates through a directory containing HTML-exported chapters and
	# runs processChapter on each. Recursively enters subdirectories.
	def processChaptersList(self, inputPath, chapters):

		# Process each chapter individually
		for filename in chapters:

			# Chapters might be organized into further subdirectories; don't miss them!
			if (os.path.isdir(inputPath + '/' + filename)):
				self.processChaptersList(inputPath + '/' + filename, os.listdir(inputPath + '/' + filename))

			else:

				try:
					inputText = open(inputPath + '/' + filename, 'r').read()
					self.processChapter(inputText)

				except IOError:
					raise Exception('Failed to write one or more chapters.')

				except:
					raise Exception('Failed to process one or more chapters.')
