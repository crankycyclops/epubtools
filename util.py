# -*- coding: utf-8 -*-

import os, sys, re, zipfile

# Like print(), but outputs to stderr.
# Stolen from: http://stackoverflow.com/questions/5574702/how-to-print-to-stderr-in-python
def eprint(*args, **kwargs):
	print(*args, file = sys.stderr, **kwargs)

# Yields a natural instead of strictly alphabetical string sort.
# Stolen from: http://stackoverflow.com/questions/4836710/does-python-have-a-built-in-function-for-string-natural-sort
def natural_sort(l):
	convert = lambda text: int(text) if text.isdigit() else text.lower() 
	alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	return sorted(l, key = alphanum_key)

# A special ZIP method that can be used to generate a ZIP file with some files
# compressed and others uncompressed. This is a requirement for ePub, which
# requires something like the following two commands on the command line:
# zip -0X <zipfile> mimetype
# zip -r9 <zipfile> OEBPS META-INF
# Modified from code found here: http://sw32.com/use-python-to-generate-epub-standard-zip-file/
def zipdirs(paths, zipFilename, baseDir, compressFile = True):

	# Zips an entire directory
	def zipdir(path, zipf, compressFile = True):

		for root, dirs, files in os.walk(path):

			for file in files:

				path = os.path.join(root, file)
				relativePath = path.replace(baseDir, '')

				if compressFile:
					zipf.write(path, relativePath, compress_type = zipfile.ZIP_DEFLATED)
				else:
					zipf.write(path, relativePath, compress_type = zipfile.ZIP_STORED)

	##########################################################################

	# Zips an individual file
	def zipafile(path, zipf, compressFile = True):

		relativePath = path.replace(baseDir, '')

		if compressFile:
			zipf.write(path, relativePath, compress_type = zipfile.ZIP_DEFLATED)
		else:
			zipf.write(path, relativePath, compress_type = zipfile.ZIP_STORED)

	##########################################################################

	# Make sure we don't overwrite an existing ZIP archive...
	if os.path.isfile(zipFilename):
		zipf = zipfile.ZipFile(zipFilename, 'a')
	else:
		zipf = zipfile.ZipFile(zipFilename, 'w')

	# We were only given one file or directory to add
	if type(paths) is str:

		if not os.path.isdir(paths):
			zipafile(paths, zipf, compressFile)
		else:
			zipdir(paths, zipf, compressFile)

	# We were passed a list of paths, so add each one
	elif type(paths) is list:

		for path in paths:

			if not os.path.isdir(path):
				zipafile(path, zipf, compressFile)
			else:
				zipdir(path, zipf, compressFile)

	else:
		raise Exception('Unsupported argument type passed to zipdirs()')
