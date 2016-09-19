# -*- coding: utf-8 -*-

import re, os, sys, subprocess
import util, driver

class Abiword(driver.Driver):

	specialChars = {
		"'":        "&#8217;", #rsquo
		"{`}":      "&#8216;", #lsquo
		"''":       "&#8221;", #rdquo
		"{``}":     "&#8220;", #ldquo
		"\ldots{}": "&#8230;", #hellip
		"---":      "&#8212;", #mdash
		"--":       "&#8211;", #ndash
		"™":        "&#8482;", #trade
		"©":        "&#169;",  #copy
		"®":        "&#174;"   #reg
	}

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, coverPath, tmpLocation)

		# Where we save the intermediate latex file
		try:
			self.latexPath = self.tmpOutputDir + '_input'
			os.mkdir(self.latexPath)
		except:
			raise Exception('Could not create temporary input directory. This is a bug.')

	##########################################################################

	# Note that we're supposed to set a value for chaptersList, but since we
	# don't really use it, the default value of False is good enough and we're
	#  not going to bother doing more with it.
	def openDriver(self):

		# Make sure the input file exists
		if not os.path.isfile(self.inputPath):
			raise Exception('Input file ' + self.inputPath + ' does not exist.')

	##########################################################################

	def cleanup(self):

		try:
			shutil.rmtree(self.latexPath)
			super().cleanup()

		# We should at least still try to let the base class run its cleanup.
		except:
			super().cleanup()

	##########################################################################

	# Processes a chapter from any document type that Abiword can read (.doc,
	# .docx, .rtf, etc.) and transforms it into ePub friendly XHTML.
	def transformChapter(self, inputText):

		inParagraph = False
		nextParagraph = ''
		paragraphs = []

		# First, extract out each paragraph
		lines = inputText.split('\n')
		for i in range(0, len(lines)):

			if inParagraph:
				if '\\end{flushleft}' == lines[i] or '\\end{flushright}' == lines[i] or '\\end{center}' == lines[i]:
					paragraphs.append('<p>' + nextParagraph + '</p>')
					nextParagraph = ''
					inParagraph = False
				else:
					nextParagraph += lines[i]

			else:
				if '\\begin{flushleft}' == lines[i] or '\\begin{flushright}' == lines[i] or '\\begin{center}' == lines[i]:
					inParagraph = True

		emphRegex = re.compile('\\\\emph{(.*?)}')
		boldRegex = re.compile('\\\\textbf{(.*?)}')
		underlineRegex = re.compile('\\\\uline{(.*?)}')

		for i in range(0, len(paragraphs)):

			# Next, replace latex constructs inside each paragraph with XHTML equivalents
			paragraphs[i] = emphRegex.sub(r'<em>\1</em>', paragraphs[i])
			paragraphs[i] = boldRegex.sub(r'<strong>\1</strong>', paragraphs[i])
			paragraphs[i] = underlineRegex.sub(r'<span style="font-decoration: underline;">\1</span>', paragraphs[i])

			# Now, replace common Latex entities with XHTML entities (this won't catch everything)
			for char in self.specialChars.keys():
				paragraphs[i] = paragraphs[i].replace(char, self.specialChars[char])

			print(paragraphs[i])
			sys.exit(1)

		invalidSlugCharsRegex = re.compile('[^a-zA-Z0-9]')

		return {
			'chapter': paragraphs[0],
			'chapterSlug': invalidSlugCharsRegex.sub('', paragraphs[0]),
			'text': inputText
		}

	##########################################################################

	# Makes an external call to abiword, which reads the input file and outputs
	# it as a latex file that we can parse much more easily.
	def processChaptersList(self, inputPath, chapters):

		latexFilePath = self.latexPath + '/input.tex'

		try:

			output = subprocess.check_output(['abiword', self.inputPath, '--to=latex', '-o', latexFilePath])

			if output:
				raise Exception()

			texLines = open(latexFilePath, 'r').readlines()

		except:
			raise Exception('Failed to convert input document. This is a bug.')

		chapterText = '';

		for i in range(0, len(texLines)):

			# Chapter break; process the next chapter
			if '\\newpage\n' == texLines[i]:
				self.processChapter(chapterText)
				chapterText = ''; # Reset inputText for the next chapter

			else:
				chapterText += texLines[i]

		# Make sure we don't skip over the last chapter ;)
		self.processChapter(chapterText)
