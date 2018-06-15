# -*- coding: utf-8 -*-

class EpubtoolException(Exception):

    pass

###############################################################################

# An error occurred in the input driver
class InputException(EpubtoolException):

	pass

###############################################################################

# An error occurred in the output driver
class OutputException(EpubtoolException):

	pass

