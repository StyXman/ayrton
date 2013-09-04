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

import ayrton
import os
import paramiko
from ayrton.expansion import bash

class cd (object):
    def __init__ (self, dir):
        self.old_dir= os.getcwd ()
        os.chdir (dir)

    def __enter__ (self):
        pass

    def __exit__ (self, *args):
        os.chdir (self.old_dir)

def export (**kwargs):
    for k, v in kwargs.items ():
        # NOTE: this is quasi ugly
        ayrton.runner.globals[k]= str (v)
        ayrton.runner.environ[k]= str (v)

def unset (*args):
    for k in args:
        if k in ayrton.runner.environ.keys ():
            # found, remove it
            del ayrton.runner.globals[k]
            del ayrton.runner.environ[k]

def run (path, *args, **kwargs):
    c= ayrton.CommandWrapper._create (path)
    return c (*args, **kwargs)

class ssh (object):
    # TODO: inherit CommandWrapper?
    # TODO: see foo.txt
    "Uses the same arguments as paramiko.SSHClient.connect ()"
    def __init__ (self, code, *args, **kwargs):
        self.code= code
        self.args= args
        self.kwargs= kwargs

    def __enter__ (self):
        self.client= paramiko.SSHClient ()
        self.client.load_host_keys (bash ('~/.ssh/known_hosts')[0])
        self.client.connect (*self.args, **self.kwargs)

        command= '''python3 -c "import pickle
from ast import Module, Assign, Name, Store, Call, Load, Expr
import sys
c= pickle.loads (sys.stdin.buffer.read (%d))
code= compile (c, 'remote', 'exec')
exec (code)"''' % len (self.code)
        (i, o, e)= self.client.exec_command (command)
        i.write (self.code)
        return (i, o, e)

    def __exit__ (self, *args):
        pass
