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
import pickle

# NOTE: all this code is excuted in the script's environment

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
        ayrton.runner.environ.globals[k]= str (v)
        ayrton.runner.environ.os_environ[k]= str (v)

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
        # get the locals from the runtime
        local_env= pickle.dumps (ayrton.runner.environ.locals)

        command= '''python3 -c "import pickle
from ast import Module, Assign, Name, Store, Call, Load, Expr
import sys
c= pickle.loads (sys.stdin.buffer.read (%d))
code= compile (c, 'remote', 'exec')
l= pickle.loads (sys.stdin.buffer.read (%d))
exec (code, {}, l)"''' % (len (self.code), len (local_env))
        (i, o, e)= self.client.exec_command (command)
        i.write (self.code)
        i.write (local_env)
        return (i, o, e)

    def __exit__ (self, *args):
        pass

def unset (*args):
    for k in args:
        if k in ayrton.runner.environ.globals.keys ():
            # found, remove it
            del ayrton.runner.environ.globals[k]
            del ayrton.runner.environ.os_environ[k]
