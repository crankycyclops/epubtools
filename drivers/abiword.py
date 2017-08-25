# -*- coding: utf-8 -*-

import re, os, sys, subprocess, shutil, collections
import util, driver

class Abiword(driver.Driver):

	# Will keep track of chapter slugs so we can append a number to make it
	# unique if necessary
	chapterSlugs = {}

	# Note that order is important here!
	specialChars = collections.OrderedDict()

	specialChars["&"]        = ""         # get rid of these
	specialChars["''"]       = "&#8221;"   #rdquo
	specialChars["\\'{a}"]   = "&#225;"    #Acute accented a
	specialChars["\\'{e}"]   = "&#233;"    #Acute accented e
	specialChars["\\'{i}"]   = "&#237;"    #Acute accented i
	specialChars["\\'{o}"]   = "&#243;"    #Acute accented o
	specialChars["\\'{u}"]   = "&#250;"    #Acute accented u
	specialChars["\\'{y}"]   = "&#253;"    #Acute accented y
	specialChars["\\'{A}"]   = "&#193;"    #Acute accented A
	specialChars["\\'{E}"]   = "&#201;"    #Acute accented E
	specialChars["\\'{I}"]   = "&#205;"    #Acute accented I
	specialChars["\\'{O}"]   = "&#211;"    #Acute accented O
	specialChars["\\'{U}"]   = "&#218;"    #Acute accented U
	specialChars["\\'{Y}"]   = "&#221;"    #Acute accented Y
	specialChars["\\`{a}"]   = "&#224;"    #Grave accented a
	specialChars["\\`{e}"]   = "&#232;"    #Grave accented e
	specialChars["\\`{i}"]   = "&#236;"    #Grave accented i
	specialChars["\\`{o}"]   = "&#242;"    #Grave accented o
	specialChars["\\`{u}"]   = "&#249;"    #Grave accented u
	specialChars["\\`{y}"]   = "&#7923;"   #Grave accented y
	specialChars["\\`{A}"]   = "&#192;"    #Grave accented A
	specialChars["\\`{E}"]   = "&#200;"    #Grave accented E
	specialChars["\\`{I}"]   = "&#204;"    #Grave accented I
	specialChars["\\`{O}"]   = "&#210;"    #Grave accented O
	specialChars["\\`{U}"]   = "&#217;"    #Grave accented U
	specialChars["\\`{Y}"]   = "&#7922;"   #Grave accented Y
	specialChars["'"]        = "&#8217;"  #rsquo
	specialChars["\\~{n}"]   = "&#241;"   #ntilde
	specialChars["\\~{N}"]   = "&#209;"   #Ntilde
	specialChars["{`}"]      = "&#8216;"  #lsquo
	specialChars["{``}"]     = "&#8220;"  #ldquo
	specialChars["\ldots{}"] = "&#8230;"  #hellip
	specialChars["---"]      = "&#8212;"  #mdash
	specialChars["™"]        = "&#8482;"  #trade
	specialChars["©"]        = "&#169;"   #copy
	specialChars["®"]        = "&#174;"   #reg
	specialChars["\$"]       = "$"        # Dollar sign
	specialChars["\&"]       = "&#38;"    #ampersand
	specialChars["\{"]       = "&#123;"   #left brace (entity prevents regex conflict later)
	specialChars["\}"]       = "&#125;"   #right brace (entity prevents regex conflict later)
	specialChars["--"]       = "&#8211;"  #ndash
	specialChars["\\\\"]     = "<br />"   #Line break
	specialChars["<"]        = "&#60;"    #lt
	specialChars["="]        = "&#61;"    #equal
	specialChars[">"]        = "&#62;"    #gt

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
		inPlainText = False

		# If we're in an unmarked plain text paragraph, we need to split off the
		# first line of the first paragraph and treat it as a separate paragraph
		# so it can be used for a reasonably sane chapter heading. This lets us
		# know, if we enter a plain text paragraph, whether or not we've
		# encountered the first non-blank paragraph already.
		foundFirstParagraph = False

		nextParagraph = ''
		paragraphs = []

		beginParagraphRegex = re.compile('(\\\\begin{flushleft}({.*?})*|\\\\begin{flushright}({.*?})*|\\\\begin{center}({.*?})*|\\\\begin{spacing}({.*?})*)')
		endParagraphRegex = re.compile('(\\\\end{flushleft}|\\\\end{flushright}|\\\\end{center}|\\\\end{spacing})')

		# First, extract out each paragraph
		lines = inputText.split('\n')
		for i in range(0, len(lines)):

			# Replace common Latex entities with XHTML entities (this won't catch
			# everything.) This goes here because it should happen before we
			# enclose the line in <p> tags.
			for char in self.specialChars.keys():
				lines[i] = lines[i].replace(char, self.specialChars[char])

			# Hack: this is dumb, but I can't figure out why some <br /> tags
			# are having their < and > values changed to entities, so I'm just
			# going to be lazy here and fix what gets changed rather than dig
			# and figure out what I did wrong ;)
			lines[i] = lines[i].replace('&#60;br /&#62;', '<br />')

			if inParagraph:

				# The beginning of a marked paragraph signals the end of a plain
				# text block. We also need to end the paragraph if we've passed
				# the first line of an unmarked plain text block, as this will
				# be used as the chapter heading.
				if inPlainText and (re.match(beginParagraphRegex, lines[i]) or (not foundFirstParagraph and len(lines[i].strip()) > 0)):
					paragraphs.append('<p>' + nextParagraph + '</p>')
					nextParagraph = ''
					inParagraph = False
					inPlainText = False
					foundFirstParagraph = True

					# Little hack so we can re-detect the beginning of the
					# marked paragraph
					if re.match(beginParagraphRegex, lines[i]):
						i = i - 1

				# We're ending a marked paragraph
				elif re.match(endParagraphRegex, lines[i]):
					paragraphs.append('<p>' + nextParagraph + '</p>')
					nextParagraph = ''
					inParagraph = False
					if len(lines[i].strip()) > 0:
						foundFirstParagraph = True

				# We're continuing an existing paragraph
				elif not inPlainText or len(lines[i].lstrip()) > 0 and lines[i].lstrip()[0] != '\\' and lines[i].lstrip()[0] != '%':
					nextParagraph += lines[i]
					if inPlainText:
						nextParagraph += '<br />\n'

			else:

				# We just entered a marked paragraph
				if re.match(beginParagraphRegex, lines[i]):
					inParagraph = True
					inPlainText = False

				# We just entered an unmarked plain text block that we're going
				# to treat the same as a paragraph (poor formatting on the part
				# of the author, whatcha goin' to do...?)
				elif len(lines[i].lstrip()) > 0 and lines[i].lstrip()[0] != '\\' and lines[i].lstrip()[0] != '%':
					nextParagraph += lines[i] + '<br />\n'
					inParagraph = True
					inPlainText = True

		# We get here if the entire chapter is one long plain text block, or if
		# a \newpage was encountered in the middle of a paragraph and is thus
		# not properly terminated.
		if inParagraph:
			paragraphs.append('<p>' + nextParagraph + '</p>')
			nextParagraph = ''
			inParagraph = False

		# Make sure we didn't encounter a blank chapter, which should be skipped
		if 0 == len(paragraphs):
			return False

		emphRegex = re.compile('\\\\emph{(.*?)}')
		boldRegex = re.compile('\\\\textbf{(.*?)}')
		underlineRegex = re.compile('\\\\uline{(.*?)}')
		textttRegex = re.compile('\\\\texttt{(.*?)}')
		spacingRegex = re.compile('\\\\begin{spacing}{.*?}(.*?)\\\\end{spacing}')
		hypertargetRegex = re.compile('\\\\hypertarget{.*?}{(.*?)}')

		# One of the DOCX files I tested with ended up marking every paragraph \large.
		# It looks like this has to do with font size. We're ignoring font size, so
		# just strip these out.
		textSizeRegex = re.compile('{(\\\\large|\\\\Large|\\\\normalsize)\s+(.*?)}')

		# Ignore text colors
		textColorRegex = re.compile('\\\\textcolor\[rgb\]{\d+.\d+,\s*\d+.\d+,\s*\d+.\d+}{(.*?)}')

		# As far as I can tell, this is Abiword f*cking up... Run these in order.
		hypertargetBrokenRegex = re.compile('\\\\hypertarget{.*?}{}(.*?)\\\\hypertarget{.*?}{')
		hypertargetBrokenRegex2 = re.compile('}(.*?)\\\\hypertarget{.*?}{')
		hypertargetBrokenRegex3 = re.compile('(.*?)\\\\hypertarget{.*?}{')

		# Detects Latex commands we don't recognize and attempts to silently
		# strip them out (perhaps a dirty trick, but it results in cleaner output)
		catchAllRegex = re.compile('\\\\[A-Za-z]+({.*?})*')

		invalidSlugCharsRegex = re.compile('[^a-zA-Z0-9]')

		chapterTemplateVars = {
			'%title': self.bookTitle,
			'%chapter': '',
			'%paragraphs': ''
		}

		# Set to the index of the first non-blank paragraph, which is
		# used as the chapter heading
		chapterHeadingIndex = False

		for i in range(0, len(paragraphs)):

			# Strip out other font-related stuff
			paragraphs[i] = textSizeRegex.sub(r'\2', paragraphs[i])
			paragraphs[i] = textColorRegex.sub(r'\1', paragraphs[i])

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

			# Though the markers I'm using to identify the beginning of
			# paragraphs are valid, there may be more than one, because
			# they're really used for formatting. So if there're more than
			# one left behind, we should remove them.
			paragraphs[i] = beginParagraphRegex.sub('', paragraphs[i])
			paragraphs[i] = endParagraphRegex.sub('', paragraphs[i])

			# Strip out any lingering Latex commands we don't recognize
			while re.search(catchAllRegex, paragraphs[i]):
				paragraphs[i] = re.sub(catchAllRegex, '', paragraphs[i])

			# All user-input braces have already been converted to numeric
			# entities, so any lingering braces should be filtered out of the
			# result.
			paragraphs[i] = paragraphs[i].replace('{', '')
			paragraphs[i] = paragraphs[i].replace('}', '')

			# If it's a plain text block instead of a marked paragraph, make sure
			# to strip out the last line break
			if '<br />' in paragraphs[i]:
				paragraphs[i] = paragraphs[i][:-11]
				paragraphs[i] += '</p>'

			# Wait for the first non-empty line, and use it as the chapter heading
			if bool == type(chapterHeadingIndex):

				if len(re.compile('<p>(.*?)</p>').sub(r'\1', paragraphs[i]).strip()) > 0:

					# Strip out tags and newlines from the chapter heading
					paragraphs[i] = re.compile(r'<[^>]+>').sub('', paragraphs[i]).replace('\n', '').strip()
					chapterHeadingIndex = i

				continue

			# Add all other paragraphs to the body text
			else:
				chapterTemplateVars['%paragraphs'] += '\t\t\t\t' + paragraphs[i] + '\n'

		# We had only empty paragraphs in the whole chapter, so obviously this
		# shouldn't be counted as a chapter at all.
		if bool == type(chapterHeadingIndex):
			return False

		chapterName = paragraphs[chapterHeadingIndex]
		chapterTemplateVars['%chapter'] = chapterName

		# Create a unique slug to identify the chapter
		chapterSlug = invalidSlugCharsRegex.sub('', chapterName)

		if len(chapterSlug) > 15:
			chapterSlug = chapterSlug[:15];

		if chapterSlug in self.chapterSlugs.keys():
			self.chapterSlugs[chapterSlug] = self.chapterSlugs[chapterSlug] + 1
		else:
			self.chapterSlugs[chapterSlug] = 1

		chapterTemplateVars['%slugChapter'] = 'ch' + chapterSlug

		chapterTemplate = open(self.scriptPath + '/templates/chapter.xhtml', 'r').read()
		for var in chapterTemplateVars.keys():
			chapterTemplate = chapterTemplate.replace(var, chapterTemplateVars[var])

		return {
			'chapter': chapterName,
			'chapterSlug': chapterSlug + '_' + str(self.chapterSlugs[chapterSlug]),
			'text': chapterTemplate
		}

	##########################################################################

	# Makes an external call to abiword, which reads the input file and outputs
	# it as a latex file that we can parse.
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

			# Skip latex comments
			if '%' == texLines[i]:
				continue

			# Chapter break; process the next chapter
			if '\\newpage' in texLines[i]:

				# So, Abiword sometimes places \newpage in the middle of a block,
				# causing f**kery for both the current and the next chapter. We
				# need to massage the text a little to undo this before continuing.
				# This probably isn't Abiword's fault, but rather the fault of
				# the word processor for poorly formatting the document.
				if 0 != texLines[i].index('\\newpage'):

					prefix = texLines[i][0:texLines[i].index('\\newpage')]

					# First, make sure braces are balanced in what we have to
					# append to the current chapter.
					braces = []

					for j in range(0, len(prefix)):
						if '{' == prefix[j]:
							braces.append(j)
						elif '}' == prefix[j]:
							braces.pop()

					if len(braces):
						for j in braces:
							prefix += '}'

					chapterText += prefix

					# Next, make sure there's always a complete paragraph and
					# balanced parenthesis in the part we have to prepend to the
					# next chapter.
					if '}' == texLines[i + 1][0]:
						texLines[i + 1] = '\\begin{spacing}{1.67}'
					else:
						texLines[i + 1] = '{' + texLines[i + 1]

				self.processChapter(chapterText)
				chapterText = ''; # Reset inputText for the next chapter

			else:
				chapterText += texLines[i]

		# Make sure we don't skip over the last chapter ;)
		self.processChapter(chapterText)
