# -*- coding: utf-8 -*-

import re, os, sys, subprocess, shutil
import util, driver

class Abiword(driver.Driver):

	# Note that order is important here!
	specialChars = {
		"''":       "&#8221;", #rdquo
		"'":        "&#8217;", #rsquo
		"{`}":      "&#8216;", #lsquo
		"{``}":     "&#8220;", #ldquo
		"\ldots{}": "&#8230;", #hellip
		"---":      "&#8212;", #mdash
		"™":        "&#8482;", #trade
		"©":        "&#169;",  #copy
		"®":        "&#174;",  #reg
		"--":       "&#8211;"  #ndash
	}

	##########################################################################

	# Constructor
	def __init__(self, bookLang, bookPublisher, bookAuthor, bookTitle, pubDate,
	copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation = '/tmp'):

		super().__init__(bookLang, bookPublisher, bookAuthor, bookTitle,
			pubDate, copyrightYear, includeCopyright, isFiction, coverPath, tmpLocation)

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
	# Apparently, Abiword's conversion to Latex is a pile of s**t, so I'm
	# limited in what I can fix :'(
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
		textttRegex = re.compile('\\\\texttt{(.*?)}')
		spacingRegex = re.compile('\\\\begin{spacing}{.*?}(.*?)\\\\end{spacing}')
		hypertargetRegex = re.compile('\\\\hypertarget{.*?}{(.*?)}')

		# As far as I can tell, this is Abiword f*cking up... Run these in order.
		hypertargetBrokenRegex = re.compile('\\\\hypertarget{.*?}{}(.*?)\\\\hypertarget{.*?}{')
		hypertargetBrokenRegex2 = re.compile('}(.*?)\\\\hypertarget{.*?}{')
		hypertargetBrokenRegex3 = re.compile('(.*?)\\\\hypertarget{.*?}{')

		# These are a best guess in an attempt to clean up Abiword's mess. There will, of course,
		# be edge cases where the user intended to have unbalanced braces. Oh well, not my fault.
		# Abiword is just kind of garbage when it comes to the conversion of Word Docs to Latex.
		# This at least limits the removal to only unbalanced parenthesis at the beginning or
		# end of the string, which minimizes false positives.
		braceFixRegex1 = re.compile('(<p>[^{]+?)}</p>')
		braceFixRegex2 = re.compile('<p>{([^}]+?</p>)')

		invalidSlugCharsRegex = re.compile('[^a-zA-Z0-9]')

		chapterTemplateVars = {
			'%title': self.bookTitle,
			'%chapter': '',
			'%slugChapter': 'ch' + invalidSlugCharsRegex.sub('', paragraphs[0]),
			'%paragraphs': ''
		}

		#import pprint, sys
		#pprint.pprint(paragraphs)
		#sys.exit(0)

		# Set to the index of the first non-blank paragraph, which is
		# used as the chapter heading
		chapterHeadingIndex = False

		for i in range(0, len(paragraphs)):

			# Replace latex constructs inside each paragraph with XHTML equivalents
			paragraphs[i] = emphRegex.sub(r'<em>\1</em>', paragraphs[i])
			paragraphs[i] = boldRegex.sub(r'<strong>\1</strong>', paragraphs[i])
			paragraphs[i] = underlineRegex.sub(r'<span style="font-decoration: underline;">\1</span>', paragraphs[i])

			# Strip out \texttt if present
			paragraphs[i] = textttRegex.sub(r'\1', paragraphs[i])

			# Strip out spacing directives
			paragraphs[i] = spacingRegex.sub(r'\1', paragraphs[i])

			# Strip out hypertags if present
			paragraphs[i] = hypertargetBrokenRegex.sub(r'\1', paragraphs[i])
			paragraphs[i] = hypertargetBrokenRegex2.sub(r'\1', paragraphs[i])
			paragraphs[i] = hypertargetBrokenRegex3.sub(r'\1', paragraphs[i])
			paragraphs[i] = hypertargetRegex.sub(r'\1', paragraphs[i])

			print(paragraphs[i])

			# Attempt an imperfect fix for Abiword f**kery
			paragraphs[i] = braceFixRegex1.sub(r'\1</p>', paragraphs[i])
			paragraphs[i] = braceFixRegex2.sub(r'<p>\1', paragraphs[i])

			# Next, replace common Latex entities with XHTML entities (this won't catch everything)
			for char in self.specialChars.keys():
				paragraphs[i] = paragraphs[i].replace(char, self.specialChars[char])

			# Wait for the first non-empty line, and use it as the chapter heading
			if bool == type(chapterHeadingIndex):

				if len(re.compile('<p>(.*?)</p>').sub(r'\1', paragraphs[i]).strip()) > 0:
					chapterHeadingIndex = i

				continue

			# Add all other paragraphs to the body text
			else:
				chapterTemplateVars['%paragraphs'] += '\t\t\t\t' + paragraphs[i] + '\n'

		chapterName = paragraphs[chapterHeadingIndex].replace('<p>', '').replace('</p>', '')
		chapterTemplateVars['%chapter'] = chapterName

		chapterTemplate = open(self.scriptPath + '/templates/chapter.xhtml', 'r').read()
		for var in chapterTemplateVars.keys():
			chapterTemplate = chapterTemplate.replace(var, chapterTemplateVars[var])

		return {
			'chapter': chapterName,
			'chapterSlug': invalidSlugCharsRegex.sub('', chapterName),
			'text': chapterTemplate
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
			if '\\newpage' in texLines[i]:
				self.processChapter(chapterText)
				chapterText = ''; # Reset inputText for the next chapter

			else:
				chapterText += texLines[i]

		# Make sure we don't skip over the last chapter ;)
		self.processChapter(chapterText)
