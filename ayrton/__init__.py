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

__version__= '0.1'

class RunningCommandWrapper (sh.RunningCommand):
    def _handle_exit_code (self, code):
        try:
            super ()._handle_exit_code (code)
        except (sh.ErrorReturnCode, sh.SignalException) as e:
            pass

    def __bool__ (self):
        # in shells, a command is true if its return code was 0
        return self.exit_code ()==0

# monkey patch sh
sh.RunningCommand= RunningCommandWrapper

runner= None

# special value to signal that the output should be captured
# instead of going to stdout
Capture= (42, )

class CommandWrapper (sh.Command):
    # this class changes the behaviour of sh.Command
    # so is more shell scripting freindly
    def __call__ (self, *args, **kwargs):
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
        kwargs['_env']= runner.environ

        return super ().__call__ (*args, **kwargs)

class cd (object):
    def __init__ (self, dir):
        self.old_dir= os.getcwd ()
        os.chdir (dir)

    def __enter__ (self):
        pass

    def __exit__ (self, *args):
        os.chdir (self.old_dir)

class Globals (dict):
    def __init__ (self):
        super ().__init__ ()
        # TODO: this is ugly
        polute (self)

    def __getitem__ (self, k):
        try:
            ans= getattr (builtins, k)
        except AttributeError:
            try:
                ans= super ().__getitem__ (k)
            except KeyError:

                ans= CommandWrapper._create (k)

        return ans

class Ayrton (object):
    def __init__ (self, script=None, file=None, **kwargs):
        if script is None and file is not None:
            script= open (file).read ()
        else:
            file= 'arg_to_main'

        self.source= compile (script, file, 'exec')
        self.globals= Globals ()

        # dict to hold the environ used for executed programs
        self.environ= os.environ.copy ()

    def run (self):
        exec (self.source, self.globals)

def polute (d):
    # these functions will be loaded from each module and put in the globals
    # tuples (src, dst) renames function src to dst
    builtins= {
        'os': [ ('getcwd', 'pwd'), 'uname', 'chmod', 'chown',
                'link', 'listdir', 'mkdir', 'remove' ],
        'time': [ 'sleep', ],
        'sys': [ 'exit' ],

        'ayrton.file_test': [ '_a', '_b', '_c', '_d', '_e', '_f', '_g', '_h',
                              '_k', '_p', '_r', '_s', '_u', '_w', '_x', '_L',
                              '_N', '_S', '_nt', '_ot' ],
        'ayrton.expansion': [ 'bash', ],
        'ayrton.functions': [ 'export', 'run', ],
        'ayrton': [ 'Capture', 'cd', ],
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

    # now envvars
    for k, v in os.environ.items ():
        d[k]= v

    # particular handling of sys.argv
    d['argv']= sys.argv[:].pop (0) # copy and remove first element, normally ayrton's or Python's path

    # now the IO files
    for std in ('stdin', 'stdout', 'stderr'):
        d[std]= getattr (sys, std).buffer

def main (script=None, file=None, **kwargs):
    global runner
    runner= Ayrton (script, file, **kwargs)
    runner.run ()
