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
from threading import Thread
import sys
import subprocess
import errno
import ctypes

import logging
logger= logging.getLogger ('ayrton.functions')

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

class ShutUpPolicy (paramiko.MissingHostKeyPolicy):
    def missing_host_key (self, *args, **kwargs):
        pass

class CopyThread (Thread):
    def __init__ (self, src, dst):
        super ().__init__ ()
        # so I can close them at will
        self.src= open (os.dup (src.fileno ()), 'rb')
        self.dst= open (os.dup (dst.fileno ()), 'wb')

    def run (self):
        # NOTE: OSError: [Errno 22] Invalid argument
        # os.sendfile (self.dst, self.src, None, 0)
        # and splice() is not available
        # so, copy by hand
        while True:
            data= self.src.read (10240)
            if len (data)==0:
                break
            else:
                self.dst.write (data)

        self.src.close ()
        self.dst.close ()

class RemoteStub:
    def __init__ (self, i, o, e):
        self.i= i
        self.o= o
        self.e= e

    def close (self):
        for attr in ('i', 'o', 'e'):
            f= getattr (self, attr)
            try:
                f.close ()
            except OSError as e:
                if e.errno!=errno.EBADF:
                    raise

class remote:
    "Uses the same arguments as paramiko.SSHClient.connect ()"
    def __init__ (self, ast, hostname, *args, **kwargs):
        def param (param, kwargs, default_value=False):
            """gets a param from kwargs, or uses a default_value. if found, it's
            removed from kwargs"""
            if param in kwargs:
                value= kwargs[param]
                del kwargs[param]
            else:
                value= default_value
            setattr (self, param, value)

        # actually, it's not a proper ast, it's the pickle of such thing
        self.ast= ast
        self.hostname= hostname
        self.args= args
        self.python_only= False

        param ('_debug', kwargs)
        self.kwargs= kwargs

        # socket/transport where the result is going to come back
        self.result_channel= None

    def __enter__ (self):
        # get the globals from the runtime

        # for solving the import problem:
        # _pickle.PicklingError: Can't pickle <class 'module'>: attribute lookup builtins.module failed
        # there are two solutions. either we setup a complex system that intercepts
        # the imports and hold them in another ayrton.Environment attribute
        # or we just weed them out here. so far this is the simpler option
        # but forces the user to reimport what's going to be used in the remote
        g= dict ([ (k, v) for k, v in ayrton.runner.globals.items ()
                          if type (v)!=types.ModuleType and k not in ('stdin', 'stdout', 'stderr') ])

        # get the locals from the runtime
        # this is not so easy: for some reason, ayrton.runner.locals is not up to
        # date in the middle of the execution (remember *this* code is executed
        # via exec() in Ayrton.run_code())
        # another option is to go through the frames
        inception_locals= sys._getframe().f_back.f_locals

        l= dict ([ (k, v) for (k, v) in inception_locals.items ()
                          if type (v)!=types.ModuleType and k not in ('ayrton_main', )])

        # special treatment for argv
        g['argv']= ayrton.runner.globals['argv']
        # l['argv']= ayrton.runner.globals['argv']

        logger.debug2 ('globals passed to remote: %s', g)
        global_env= pickle.dumps (g)
        logger.debug ('locals passed to remote: %s', l)
        local_env= pickle.dumps (l)

        port= 4227

        command= '''python3 -c "#!                                          #  1
import pickle                                                               #  2
# names needed for unpickling                                               #  3
from ast import Module, Assign, Name, Store, Call, Load, Expr               #  4
import sys                                                                  #  5
from socket import socket                                                   #  6
import ayrton #  this means that ayrton has to be installed in the remote   #  7
                                                                            #  8
import logging                                                              #  9
logger= logging.getLogger ('ayrton.remote')                                 # 10
                                                                            # 11
ast= pickle.loads (sys.stdin.buffer.read (%d))                              # 12
logger.debug ('code to run:\\n%%s', ayrton.ast_pprinter.pprint (ast))       # 13
g= pickle.loads (sys.stdin.buffer.read (%d))                                # 14
logger.debug2 ('globals received: %%s', g)                                  # 15
l= pickle.loads (sys.stdin.buffer.read (%d))                                # 16
logger.debug ('locals received: %%s', l)                                    # 17
                                                                            # 18
runner= ayrton.Ayrton (g, l)                                                # 19
caught= None                                                                # 20
result= None                                                                # 21
                                                                            # 22
try:                                                                        # 23
    result= runner.run_tree (ast, 'from_remote')                            # 24
except Exception as e:                                                      # 25
    logger.debug ('run raised: %%r', e)                                     # 26
    caught= e                                                               # 27
                                                                            # 28
logger.debug ('runner.locals: %%s', runner.locals)                          # 29
                                                                            # 30
client= socket ()                                                           # 31
client.connect (('127.0.0.1', %d))                                          # 32
client.sendall (pickle.dumps ( (runner.locals, result, caught) ))           # 33
client.close ()"                                                            # 34
''' % (len (self.ast), len (global_env), len (local_env), port)

        logger.debug ('code to execute remote: %s', command)

        if not self._debug:
            self.client= paramiko.SSHClient ()
            # self.client.load_host_keys (bash ('~/.ssh/known_hosts'))
            # self.client.set_missing_host_key_policy (ShutUpPolicy ())
            self.client.set_missing_host_key_policy (paramiko.WarningPolicy ())
            self.client.connect (self.hostname, *self.args, **self.kwargs)

            # create the backchannel
            self.result_channel= self.client.get_transport ()
            self.result_channel.request_port_forward ('localhost', port)

            (i, o, e)= self.client.exec_command (command)
        else:
            # to debug, run
            # nc -l -s 127.0.0.1 -p 2233 -vv -e /bin/bash
            self.client= socket ()
            self.client.connect ((self.hostname, 2233))
            # unbuffered
            i= open (self.client.fileno (), 'wb', 0)
            o= open (self.client.fileno (), 'rb', 0)
            e= open (self.client.fileno (), 'rb', 0)

            i.write (command.encode ())

            self.result_channel= socket ()
            # self.result_channel.setsockopt (SO_REUSEADDR, )
            self.result_channel.bind (('', port))
            self.result_channel.listen (1)

        logger.debug ('sending ast, globals, locals')
        i.write (self.ast)
        i.write (global_env)
        i.write (local_env)

        # TODO: setup threads with sendfile() to fix i,o,e API

        return RemoteStub(i, o, e)

    def __exit__ (self, *args):
        if self._debug:
            (conn, addr)= self.result_channel.accept ()
            self.result_channel.close ()
        else:
            conn= self.result_channel.accept ()

        data= b''
        partial= conn.recv (8196)
        while len(partial)>0:
            data+= partial
            partial= conn.recv (8196)

        (l, result, e)= pickle.loads (data)
        logger.debug ('result from remote: %r', result)
        logger.debug ('locals returned from remote: %s', l)
        conn.close ()

        # update locals
        callers_frame= sys._getframe().f_back
        logger.debug ('caller name: %s', callers_frame.f_code.co_name)
        callers_frame.f_locals.update (l)
        # see https://mail.python.org/pipermail/python-dev/2005-January/051018.html
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(callers_frame), 0)

        # TODO: (and globals?)

        logger.debug2 ('globals after remote: %s', ayrton.runner.globals)
        logger.debug ('locals after remote: %s', callers_frame.f_locals)
        logger.debug2 ('locals: %d', id (ayrton.runner.locals))
        if e is not None:
            logger.debug ('raised from remote: %r', e)
            raise e

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

def unset (*args):
    for k in args:
        if k in ayrton.runner.globals.keys ():
            # found, remove it
            del ayrton.runner.globals[k]
            del os.environ[k]
