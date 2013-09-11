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
import sh
import importlib
import builtins
import ast
from ast import Pass, Module, Bytes, copy_location, Call, Name, Load
from ast import fix_missing_locations, Import, alias
import pickle

__version__= '0.1.2'

class RunningCommandWrapper (sh.RunningCommand):
    def _handle_exit_code (self, code):
        try:
            super ()._handle_exit_code (code)
        except (sh.ErrorReturnCode, sh.SignalException) as e:
            pass

    def __bool__ (self):
        # in shells, a command is true if its return code was 0
        return self.exit_code==0

# monkey patch sh
sh.RunningCommand= RunningCommandWrapper

# singleton
runner= None

# special value to signal that the output should be captured
# instead of going to stdout
Capture= (42, )

class CommandWrapper (sh.Command):
    # this class changes the behaviour of sh.Command
    # so is more shell scripting freindly
    def __call__ (self, *args, **kwargs):
        if ('_out' in kwargs.keys () and kwargs['_out']==Capture and
                not '_tty_out' in kwargs.keys ()):
            # for capturing, the default is to not simulate a tty
            kwargs['_tty_out']= False

        # if _out or _err are not provided, connect them to the original ones
        for std, buf in [('_out', sys.stdout.buffer), ('_err', sys.stderr.buffer)]:
            if not std in kwargs:
                kwargs[std]= buf
            # the following two messes sh's semantic for _std==None
            elif kwargs[std] is None:
                kwargs[std]= '/dev/null'
            elif kwargs[std]==Capture:
                kwargs[std]= None

        # mess with the environ
        global runner
        kwargs['_env']= runner.environ.os_environ

        return super ().__call__ (*args, **kwargs)

class Environment (object):
    def __init__ (self, globals=None, locals=None):
        super ().__init__ ()

        if globals is None:
            self.globals= {}
        else:
            self.globals= globals

        if locals is None:
            self.locals= {}
        else:
            self.locals= locals

        self.python_builtins= builtins.__dict__.copy ()
        self.ayrton_builtins= {}
        polute (self.ayrton_builtins)
        self.os_environ= os.environ.copy ()

    def __getitem__ (self, k):
        strikes= 0
        for d in (self.locals, self.globals, self.os_environ,
                  self.python_builtins, self.ayrton_builtins):
            try:
                ans= d[k]
                # found, don't search anymore (just in case you could find it
                # somewhere else)
                break
            except KeyError:
                strikes+= 1

        if strikes==5:
            # the name was not found in any of the dicts
            # create a command for it
            ans= CommandWrapper._create (k)

        return ans

    def __setitem__ (self, k, v):
        self.locals[k]= v

    def __iter__ (self):
        return self.locals.__iter__ ()

    def __str__ (self):
        return str ([ self.globals, self.locals, self.os_environ ])

class CrazyASTTransformer (ast.NodeTransformer):

    def visit_With (self, node):
        call= node.items[0].context_expr
        # TODO: more checks
        if call.func.id=='ssh':
            # capture the body and put it as the first argument to ssh()
            # but within a module, and already pickled;
            # otherwise we need to create an AST for the call of all the
            # constructors in the body we capture... it's complicated
            m= Module (body=node.body)

            data= pickle.dumps (m)
            s= Bytes (s=data)
            s.lineno= node.lineno
            s.col_offset= node.col_offset
            call.args.insert (0, s)

            p= Pass ()
            p.lineno= node.lineno+1
            p.col_offset= node.col_offset+4

            node.body= [ p ]

        return node

class Ayrton (object):
    def __init__ (self, script=None, file=None, tree=None, globals=None,
                  locals=None, **kwargs):
        if script is None and file is not None:
            script= open (file).read ()
        else:
            file= 'arg_to_main'

        if script is not None:
            tree= ast.parse (script)
            tree= CrazyASTTransformer().visit (tree)

        self.source= compile (tree, file, 'exec')
        self.environ= Environment (globals, locals)

    def run (self):
        exec (self.source, self.environ.globals, self.environ)

def polute (d):
    # these functions will be loaded from each module and put in the globals
    # tuples (src, dst) renames function src to dst
    builtins= {
        'os': [ ('getcwd', 'pwd'), 'uname', 'listdir', ],
        'os.path': [ 'abspath', 'basename', 'commonprefix', 'dirname',  ],
        'time': [ 'sleep', ],
        'sys': [ 'argv', 'exit' ],

        'ayrton.file_test': [ '_a', '_b', '_c', '_d', '_e', '_f', '_g', '_h',
                              '_k', '_p', '_r', '_s', '_u', '_w', '_x', '_L',
                              '_N', '_S', '_nt', '_ot' ],
        'ayrton.expansion': [ 'bash', ],
        'ayrton.functions': [ 'cd', 'export', 'run', 'ssh', 'unset', ],
        'ayrton': [ 'Capture', ],
        'sh': [ 'CommandNotFound', ],
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

def run (tree, globals, locals):
    global runner
    runner= Ayrton (tree=tree, globals=globals, locals=locals)
    runner.run ()

def main (script=None, file=None, **kwargs):
    global runner
    runner= Ayrton (script=script, file=file, **kwargs)
    runner.run ()
