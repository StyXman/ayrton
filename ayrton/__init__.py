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

__version__= '0.1a'

class RunningCommandWrapper (sh.RunningCommand):
    def _handle_exit_code (self, code):
        self.code= code
        try:
            super ()._handle_exit_code (code)
        except (sh.ErrorReturnCode, sh.SignalException) as e:
            pass

    def __bool__ (self):
        # in shells, a command is true if its return code was 0
        return self.code==0

# monkey patch sh
sh.RunningCommand= RunningCommandWrapper

# dict to hold the environ used for executed programs
environ= os.environ.copy ()

class CommandWrapper (sh.Command):
    # this class changes the behaviour of sh.Command
    # so is more shell scripting freindly
    def __call__ (self, *args, **kwargs):
        # if _out or _err are not provided, connect them to the original ones
        if not '_out' in kwargs:
            kwargs['_out']= sys.stdout.buffer
        if not '_err' in kwargs:
            kwargs['_err']= sys.stderr.buffer

        # mess with the environ
        kwargs['_env']= environ

        return super ().__call__ (*args, **kwargs)

def polute (d):
    # these functions will be loaded from each module and put in the globals
    builtins= {
        'os': [ 'chdir', 'getcwd', 'uname', 'chmod', 'chown', 'link', 'listdir',
                'mkdir', 'remove' ],
        'time': [ 'sleep', ],
        'sys': [ 'exit' ],

        'ayrton.file_test': [ '_a', '_b', '_c', '_d', '_e', '_f', '_g', '_h',
                              '_k', '_p', '_r', '_s', '_u', '_w', '_x', '_L',
                              '_N', '_S', '_nt', '_ot' ],
        'ayrton.expansion': [ 'bash', ],
        'ayrton.builtins': [ 'export', 'run', ],
        }

    for module, functions in builtins.items ():
        m= importlib.import_module (module)
        for function in functions:
            d[function]= getattr (m, function)

    # particular handling of sys.argv
    d['argv']= sys.argv[:].pop (0) # copy and remove first element, normally ayrton's or Python's path

    # now the IO files
    for std in ('stdin', 'stdout', 'stderr'):
        d[std]= getattr (sys, std).buffer

class Globals (dict):
    def __init__ (self):
        super ().__init__ ()
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

def main (script=None):
    if script is None:
        script= open (sys.argv[1]).read ()
        _file= sys.argv[1]
    else:
        _file= 'arg_to_main'

    s= compile (script, _file, 'exec')
    g= Globals ()
    # l= os.environ.copy ()

    # fire!
    exec (s, g)
