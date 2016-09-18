# -*- coding: utf-8 -*-

import re
import util, driver

class Scrivener(driver.Driver):

	# Constructor
	def __init__(self, bookAuthor, bookTitle, copyrightYear):
		super().__init__(bookAuthor, bookTitle, copyrightYear)

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

		return {'chapter': chapterHeading, 'text': inputText}

