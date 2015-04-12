# -*- coding: utf-8 -*-

# (c) 2013 Marcos Dione <mdione@grulic.org.ar>

# This file is part of ayrton.
#
# ayrton is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ayrton is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ayrton.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import importlib
import ast
import logging

logging.basicConfig(filename='ayrton.log',level=logging.DEBUG)
logger= logging.getLogger ('ayton')

# things that have to be defined before importing ayton.execute :(
# singleton
runner= None

from ayrton.castt import CrazyASTTransformer
from ayrton.execute import o, Command, Capture, CommandFailed

__version__= '0.4.3'

class Ayrton (object):
    def __init__ (self, globals=None, **kwargs):
        if globals is None:
            self.globals= {}
        else:
            self.globals= globals
        polute (self.globals, kwargs)

        self.options= {}
        self.pending_children= []

    def run_file (self, file):
        # it's a pity that parse() does not accept a file as input
        # so we could avoid reading the whole file
        self.run_script (open (file).read (), file)

    def run_script (self, script, file_name):
        tree= ast.parse (script)
        tree= CrazyASTTransformer (self.globals).modify (tree)

        self.run_tree (tree, file_name)

    def run_tree (self, tree, file_name):
        self.run_code (compile (tree, file_name, 'exec'))

    def run_code (self, code):
        exec (code, self.globals)

    def wait_for_pending_children (self):
        for i in range (len (self.pending_children)):
            child= self.pending_children.pop (0)
            child.wait ()

def polute (d, more):
    # TODO: weed out some stuff (copyright, etc)
    d.update (__builtins__)
    d.update (os.environ)

    # these functions will be loaded from each module and put in the globals
    # tuples (src, dst) renames function src to dst
    builtins= {
        'os': [ ('getcwd', 'pwd'), 'uname', 'listdir', ],
        'os.path': [ 'abspath', 'basename', 'commonprefix', 'dirname',  ],
        'time': [ 'sleep', ],
        'sys': [ 'exit', 'argv' ],

        'ayrton.file_test': [ '_a', '_b', '_c', '_d', '_e', '_f', '_g', '_h',
                              '_k', '_p', '_r', '_s', '_u', '_w', '_x', '_L',
                              '_N', '_S', '_nt', '_ot' ],
        'ayrton.expansion': [ 'bash', ],
        'ayrton.functions': [ 'cd', ('cd', 'chdir'), 'export', 'option', 'remote', 'run',
                               'shift', 'source', 'unset', ],
        'ayrton.execute': [ 'o', 'Capture', 'CommandFailed', 'CommandNotFound',
                            'Pipe', 'Command'],
        }

    for module, functions in builtins.items ():
        m= importlib.import_module (module)
        for function in functions:
            if type (function)==tuple:
                src, dst= function
            else:
                src= function
                dst= function

            d[dst]= getattr (m, src)

    # now the IO files
    for std in ('stdin', 'stdout', 'stderr'):
        d[std]= getattr (sys, std).buffer

    d.update (more)

def run_tree (tree, globals):
    global runner
    runner= Ayrton (globals=globals)
    runner.run_tree (tree, 'unknown_tree')

def run_file_or_script (script=None, file=None, **kwargs):
    global runner
    runner= Ayrton (**kwargs)
    if script is None:
        runner.run_file (file)
    else:
        runner.run_script (script, 'script_from_command_line')

# backwards support for unit tests
main= run_file_or_script
