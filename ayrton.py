#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

class runner (object):
    def __init__ (self, exe):
        self.exe= exe

    def __call__ (self, args):
        os.system ("%s %s" % (self.exe, args))

bi= sys.modules['__main__'].__builtins__

class namespace (object):
    def __getitem__ (self, k):
        return getattr (self, k)

    def __getattribute__ (self, k):
        # we will give precedence to builtins instead of executables
        # if an import gets in the way to an actual executable,
        # try «import foo as bar»
        try:
            # we cannot try to store bi as an attribute of self
            # otherwise we get an infinite recursion
            ans= bi.__dict__[k]
        except KeyError:
            ans= runner (k)

        return ans

if __name__=='__main__':
    sys.modules['__main__'].__builtins__= namespace ()
    ls ("-l")
