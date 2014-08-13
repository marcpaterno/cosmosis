import sys

"""
This thing is pretty cool - I found it on StackOverflow.

This is a lazily loaded module that provides an interface to pylab.

If you do:

import lazy_pylab as pylab

then you can use pylab in exactly the normal way:
pylab.plot(range(10))
etc., but pylab itself will not be loaded until the first
access of a pylab function or other attribute.

Since pylab can take a relatively long time to load this 
can save time if you never actually end up using it in a
particular run.

"""

class _LazyPylab(object):
	def __init__(self):
		self.first=True
	
	def initialize_matplotlib(self):
		import matplotlib
		matplotlib.rcParams['figure.max_open_warning'] = 100
		matplotlib.rcParams['figure.figsize'] = (8,6)
		matplotlib.rcParams['font.family']='serif'
		matplotlib.rcParams['font.size']=18
		matplotlib.rcParams['legend.fontsize']=15
		matplotlib.rcParams['xtick.major.size'] = 10.0
		matplotlib.rcParams['xtick.minor.size'] = 5.0
		matplotlib.rcParams['ytick.major.size'] = 10.0
		matplotlib.rcParams['ytick.minor.size'] = 5.0
		matplotlib.use("Agg")

	def __getattr__(self, name):
		if self.first:
			self.initialize_matplotlib()
			self.first=False
		import pylab
		return getattr(pylab, name)


sys.modules[__name__] = _LazyPylab()