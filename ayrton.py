#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

class Runner (object):
    def __init__ (self, exe):
        self.exe= exe

    def __call__ (self, args):
        os.system ("%s %s" % (self.exe, args))

bi= sys.modules['__main__'].__builtins__

class Namespace (object):
    def __getitem__ (self, k):
        # we cannot use any builting here because that leads to a infinite recursion
        try:
            ans= bi.__dict__[k]
        except bi.KeyError:
            ans= Runner (k)

        return ans

d= Namespace ()
sys.modules['__main__'].__builtins__= d
