'''
Created on 25 Feb 2013

@author: francis
'''

from optparse import OptionParser

class WellBehavedOptionParser(OptionParser):
    """
        OptionParser calls sys.exit when it gets upset, this wrapper class
        intercepts that method, and raises a value error instead.
        The optparse
        docs suggest using this approach.
    """
    def __init__(self, *args, **kwargs):
        self.exitOnError = kwargs.pop("exitOnError", True)
        # Can't use super() because OptionParser is not a new-style class
        OptionParser.__init__(self, *args, **kwargs)
    def exit(self, code=0, message=None, *args, **kwargs):
        if self.exitOnError:
            return OptionParser.exit(self, code, message, *args, **kwargs)
        raise ValueError(message)

