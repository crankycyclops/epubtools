# -*- coding: utf-8 -*-

import os, subprocess

from pyrtfdom.dom import RTFDOM
from pyrtfdom import elements

from exception import InputException
from .rtf import Rtf
from .driver import Driver
from ..domnode import EbookNode

class Soffice(Rtf):

	# Convert document format that LibreOffice/OpenOffice understands into an RTF
	def __docToRTF(self):

		try:

			filename = os.path.splitext(os.path.split(self._inputPath)[1])[0]

			output = subprocess.check_output([
				'soffice',
				'--headless',
				'--convert-to',
				'rtf',
				self._inputPath, '--outdir', self.__tmpPath
			], universal_newlines=True)

			if output.find('Error:') >= 0:
				raise InputException('Could not convert document')
			else:
				return self.__tmpPath + '/' + filename + '.rtf'

		except:
			raise InputException('Could not convert document')

	##########################################################################

	# Constructor
	def __init__(self, tmpLocation = '/tmp'):

		super().__init__()

		self.__tmpPath = tmpLocation
		self.__requiresCleanup = False

		try:
			subprocess.check_output(['soffice', '--version'])

		except:
			raise AssertionError('LibreOffice or OpenOffice executable must be installed to use the Soffice driver.')

	##########################################################################

	def open(self, filename):

		super().open(filename)

		# If it's not an RTF file, convert it to one first
		if not filename.lower().endswith('.rtf'):
			self._inputPath = self.__docToRTF()
			self.__requiresCleanup = True

	##########################################################################

	# Remove temporary files created during conversion to RTF
	def cleanup(self):

		# Only required if there was an actual document conversion (it's
		# possible an RTF was passed as an input file, in which case we just
		# pass through to the Rtf driver's methods.)
		if self.__requiresCleanup:

			try:
				if os.path.isfile(self._inputPath):
					os.remove(self._inputPath)

			# If for some reason we can't remove these files, I don't want a backend
			# process on a server to return with an error. So we'll just silently
			# fail and monitor /tmp from time to time to make sure it doesn't fill
			# up with too many files.
			except:
				pass
