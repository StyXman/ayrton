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
import paramiko
# from ayrton.expansion import bash
import pickle
import types
from socket import socket
from threading import Thread
import sys
import errno
import ctypes
import os
import traceback

import logging
logger= logging.getLogger ('ayrton.remote')

class ShutUpPolicy (paramiko.MissingHostKeyPolicy):
    def missing_host_key (self, *args, **kwargs):
        pass

class CopyThread (Thread):
    def __init__ (self, src, dst):
        super ().__init__ ()
        # so I can close them at will
        logger.debug ('CopyThread %s -> %s', src, dst)
        # self.src= open (os.dup (src.fileno ()), 'rb')
        # self.dst= open (os.dup (dst.fileno ()), 'wb')
        self.src= src
        self.dst= dst

    def run (self):
        # NOTE: OSError: [Errno 22] Invalid argument
        # os.sendfile (self.dst, self.src, None, 0)
        # and splice() is not available
        # so, copy by hand
        while True:
            try:
                data= self.src.read (10240)
                logger.debug ('%s -> %s: %s', self.src, self.dst, data)
            # ValueError: read of closed file
            except (OSError, ValueError) as e:
                logger.debug ('stopping copying thread for %s', self.src)
                logger.debug (traceback.format_exc ())
                break
            else:
                if len (data)==0:
                    logger.debug ('stopping copying thread for %s, no more data', self.src)
                    break
                else:
                    self.dst.write (data.decode ())
                    # self.dst.write (data)

        # self.close ()

    def close (self):
        logger.debug ('closing %s', self.src)
        self.src.close ()
        # self.dst.close ()

class RemoteStub:
    def __init__ (self, i, o, e):
        # TODO: handle _in, _out, _err
        # TODO: handle stdin
        self.i= i
        self.o= CopyThread (o, sys.stdout)
        self.o.start ()
        self.e= CopyThread (e, sys.stderr)
        self.e.start ()

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
        # actually, it's not a proper ast, it's the pickle of such thing
        self.ast= ast
        self.hostname= hostname
        self.args= args
        self.python_only= False

        self.param ('_debug', kwargs)
        self.param ('_test', kwargs)
        self.kwargs= kwargs

        # socket/transport where the result is going to come back
        self.result_channel= None

    def param (self, param, kwargs, default_value=False):
        """gets a param from kwargs, or uses a default_value. if found, it's
        removed from kwargs"""
        if param in kwargs:
            value= kwargs[param]
            del kwargs[param]
        else:
            value= default_value
        setattr (self, param, value)

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
                          if type (v)!=types.ModuleType and k not in ('stdin', 'stdout', 'stderr') ])

        # special treatment for argv
        g['argv']= ayrton.runner.globals['argv']

        logger.debug3 ('globals passed to remote: %s', ayrton.utils.dump_dict (g))
        global_env= pickle.dumps (g)
        logger.debug3 ('locals passed to remote: %s', ayrton.utils.dump_dict (l))
        local_env= pickle.dumps (l)

        port= 4227

        if not self._debug and not self._test:
            precommand= ''
        else:
            precommand= '''import os; os.chdir (%r)''' % os.getcwd ()

        command= '''python3 -c "#!                                        #  1
import pickle                                                             #  2
# names needed for unpickling                                             #  3
from ast import Module, Assign, Name, Store, Call, Load, Expr             #  4
import sys                                                                #  5
from socket import socket                                                 #  6
import ayrton #  this means that ayrton has to be installed in the remote #  7
import traceback                                                          #  8
                                                                          #  9
import logging                                                            # 10
logger= logging.getLogger ('ayrton.remote.runner')                        # 11
                                                                          # 12
# precommand, used by tests to change to the proper directory             # 13
# so it picks up the current version of the code.                         # 14
%s                                                                        # 15
                                                                          # 16
client= socket ()                                                         # 17
client.connect (('127.0.0.1', %d))                                        # 18
ast= pickle.loads (client.recv (%d))                                      # 19
logger.debug ('code to run:\\n%%s', ayrton.ast_pprinter.pprint (ast))     # 20
g= pickle.loads (client.recv (%d))                                        # 21
logger.debug2 ('globals received: %%s', ayrton.utils.dump_dict (g))       # 22
l= pickle.loads (client.recv (%d))                                        # 23
logger.debug2 ('locals received: %%s', ayrton.utils.dump_dict (l))        # 24
                                                                          # 25
# set the global runner so functions and Commands work                    # 26
ayrton.runner= ayrton.Ayrton (g, l)                                       # 27
caught= None                                                              # 28
result= None                                                              # 29
                                                                          # 30
try:                                                                      # 31
    result= ayrton.runner.run_tree (ast, 'from_remote')                   # 32
except Exception as e:                                                    # 33
    logger.debug ('run raised: %%r', e)                                   # 34
    logger.debug (traceback.format_exc())                                 # 35
    caught= e                                                             # 36
                                                                          # 37
logger.debug2 ('runner.locals: %%s', ayrton.utils.dump_dict (ayrton.runner.locals)) # 38
                                                                          # 39
logger.debug ('about to send exit status')                                # 40
data = pickle.dumps ( (ayrton.runner.locals, result, caught) )            # 41
logger.debug ('sending %%d bytes', len (data))                            # 42
client.sendall (data)                                                     # 43
logger.debug ('exit status sent')                                         # 44
client.close ()                                                           # 45"
''' % (precommand, port, len (self.ast), len (global_env), len (local_env))

        logger.debug ('code to execute remote: %s', command)

        if not self._debug:
            self.client= paramiko.SSHClient ()
            # TODO: TypeError: invalid file: ['/home/mdione/.ssh/known_hosts']
            # self.client.load_host_keys (bash ('~/.ssh/known_hosts'))
            # self.client.set_missing_host_key_policy (ShutUpPolicy ())
            self.client.set_missing_host_key_policy (paramiko.WarningPolicy ())
            self.client.connect (self.hostname, *self.args, **self.kwargs)

            # create the backchannel
            # this channel will be used for sending/receiving runtime data
            # to/from the remote
            # the remote code will connect to it (line #18)
            # read the ast (#19), globals (#21) and locals (#23)
            # and return the locals, result and exception (#43)
            # the remote will see this channel as a localhost port
            # and it's seen on the local side as self.con defined below
            self.result_channel= self.client.get_transport ()
            self.result_channel.request_port_forward ('localhost', port)

            (i, o, e)= self.client.exec_command (command)

            self.conn= self.result_channel.accept ()
        else:
            self.client= socket ()
            self.client.connect ((self.hostname, 2233)) # nc listening here, see DebugRemoteTests
            # unbuffered
            i= open (self.client.fileno (), 'wb', 0)
            o= open (self.client.fileno (), 'rb', 0)
            e= open (self.client.fileno (), 'rb', 0)

            self.result_channel= socket ()
            # self.result_channel.setsockopt (SO_REUSEADDR, )
            self.result_channel.bind (('', port))
            self.result_channel.listen (1)

            # so bash does not hang waiting from more input
            command+= 'exit\n'
            i.write (command.encode ())

            (self.conn, addr)= self.result_channel.accept ()

        logger.debug ('sending ast, globals, locals')
        self.conn.sendall (self.ast)
        self.conn.sendall (global_env)
        self.conn.sendall (local_env)

        self.connection= RemoteStub(i, o, e)

    def __exit__ (self, *args):
        logger.debug (args)
        data= b''
        partial= self.conn.recv (8196)
        while len(partial)>0:
            data+= partial
            partial= self.conn.recv (8196)

        logger.debug ('recieved %d bytes', len (data))
        (l, result, e)= pickle.loads (data)
        logger.debug ('result from remote: %r', result)
        logger.debug3 ('locals returned from remote: %s', ayrton.utils.dump_dict (l))
        self.conn.close ()

        # update locals
        callers_frame= sys._getframe().f_back
        logger.debug3 ('caller name: %s', callers_frame.f_code.co_name)
        callers_frame.f_locals.update (l)
        # see https://mail.python.org/pipermail/python-dev/2005-January/051018.html
        ctypes.pythonapi.PyFrame_LocalsToFast(ctypes.py_object(callers_frame), 0)
        if self._debug:
            # this makes sure that remote locals were properly store in the fast locals
            ctypes.pythonapi.PyFrame_FastToLocals(ctypes.py_object(callers_frame))

        # TODO: (and globals?)

        logger.debug3 ('globals after remote: %s', ayrton.utils.dump_dict (ayrton.runner.globals))
        logger.debug3 ('locals after remote: %s', ayrton.utils.dump_dict (callers_frame.f_locals))
        logger.debug3 ('co_varnames: %s', callers_frame.f_code.co_varnames)

        self.result_channel.close ()
        self.connection.close ()

        if e is not None:
            logger.debug ('raised from remote: %r', e)
            # TODO: this makes the exception be as if raised from here
            raise e
