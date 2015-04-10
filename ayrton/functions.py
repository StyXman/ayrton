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
import ayrton.execute
import os
import paramiko
from ayrton.expansion import bash
import pickle
import types
from socket import socket

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
        ayrton.runner.globals[k]= str (v)
        os.environ[k]= str (v)

option_map= dict (
    e= 'errexit',
    )

def option (option, value=True):
    if len (option)==2:
        if option[0]=='-':
            value= True
        elif option[0]=='+':
            value= False
        else:
            # TODO: syntax error:
            pass
        option= option_map[option[1]]

    ayrton.runner.options[option]= value

class remote (object):
    "Uses the same arguments as paramiko.SSHClient.connect ()"
    def __init__ (self, ast, hostname, *args, **kwargs):
        def param (p, d, v=False):
            if p in d:
                v= d[p]
                del d[p]
            setattr (self, p, v)

        # actually, it's not a proper ast, it's the pickle of such thing
        self.ast= ast
        self.hostname= hostname
        self.args= args
        self.python_only= False

        param ('_python_only', kwargs)
        param ('_debug', kwargs)
        self.kwargs= kwargs

    def __enter__ (self):
        # get the globals from the runtime

        # for solving the import problem:
        # _pickle.PicklingError: Can't pickle <class 'module'>: attribute lookup builtins.module failed
        # there are two solutions. either we setup a complex system that intercepts
        # the imports and hold them in another ayrton.Environment attribute
        # or we just weed them out here. so far this is the simpler option
        # but forces the user to reimport what's going to be used in the remote
        g= dict ([ (k, v) for (k, v) in ayrton.runner.globals.items ()
                   if type (v)!=types.ModuleType and k not in ('stdin', 'stdout', 'stderr') ])
        # special treatment for argv
        g['argv']= ayrton.runner.globals['argv']
        global_env= pickle.dumps (g)

        if self._python_only:
            command= '''python3 -c "import pickle
# names needed for unpickling
from ast import Module, Assign, Name, Store, Call, Load, Expr
import sys
ast= pickle.loads (sys.stdin.buffer.read (%d))
code= compile (ast, 'remote', 'exec')
g= pickle.loads (sys.stdin.buffer.read (%d))
exec (code, g, {})"''' % (len (self.ast), len (global_env))
        else:
            command= '''python3 -c "import pickle
# names needed for unpickling
from ast import Module, Assign, Name, Store, Call, Load, Expr
import sys
import ayrton
ast= pickle.loads (sys.stdin.buffer.read (%d))
g= pickle.loads (sys.stdin.buffer.read (%d))
ayrton.run_tree (ast, g)"''' % (len (self.ast), len (global_env))

        if not self._debug:
            self.client= paramiko.SSHClient ()
            # self.client.load_host_keys (bash ('~/.ssh/known_hosts'))
            # self.client.set_missing_host_key_policy (ShutUpPolicy ())
            self.client.set_missing_host_key_policy (paramiko.WarningPolicy ())
            self.client.connect (self.hostname, *self.args, **self.kwargs)

            (i, o, e)= self.client.exec_command (command)
        else:
            self.client= socket ()
            self.client.connect ((self.hostname, 2233))
            i= open (self.client.fileno (), 'wb')
            o= open (self.client.fileno (), 'rb')
            e= open (self.client.fileno (), 'rb')

            i.write (command.encode ())
            i.write (b'\n')

        i.write (self.ast)
        i.write (global_env)
        # TODO: setup threads with sendfile() to fix i,o,e API
        return (i, o, e)

    def __exit__ (self, *args):
        pass

def run (path, *args, **kwargs):
    c= ayrton.execute.Command (path)
    return c (*args, **kwargs)

def shift (n=1):
    # we start at 1 becasuse 0 is the script's path
    # this closely follows bash's behavior
    if n==1:
        ans= ayrton.runner.globals['argv'].pop (1)
    elif n>1:
        ans= [ ayrton.runner.globals['argv'].pop (1)
               for i in range (n) ]
    else:
        # TODO
        pass

    return ans

def source (file):
    # TODO: decide if source makes any sense
    sub_runner= ayrton.Ayrton ()
    sub_runner.run_file (file)
    ayrton.runner.globals.update (sub_runner.globals)

def unset (*args):
    for k in args:
        if k in ayrton.runner.globals.keys ():
            # found, remove it
            del ayrton.runner.globals[k]
            del os.environ[k]
