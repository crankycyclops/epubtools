# -*- coding: utf-8 -*-

import sys, re

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
