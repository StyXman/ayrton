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
from select import select
import io
from termios import tcgetattr, tcsetattr, TCSADRAIN
from termios import IGNPAR, ISTRIP, INLCR, IGNCR, ICRNL, IXON, IXANY, IXOFF
from termios import ISIG, ICANON, ECHO, ECHOE, ECHOK, ECHONL, IEXTEN, OPOST, VMIN, VTIME
import shutil

import logging
logger= logging.getLogger ('ayrton.remote')

class ShutUpPolicy (paramiko.MissingHostKeyPolicy):
    def missing_host_key (self, *args, **kwargs):
        pass


class InteractiveThread (Thread):
    def __init__ (self, pairs):
        super ().__init__ ()
        # so I can close them at will
        logger.debug ('%s: %s', self, pairs)
        self.pairs= pairs
        self.copy_to= dict (pairs)
        self.finished= os.pipe ()

        # we're using a tty, change all the local settings for stdin
        # directly taken from openssh (sshtty.c)
        self.orig_terminfo= tcgetattr (pairs[0][0])
        # input, output, control, local, speeds, special chars
        iflag, oflag, cflag, lflag, ispeed, ospeed, cc= self.orig_terminfo

        # turn on:
        # Ignore framing errors and parity errors
        iflag|= IGNPAR
        # turn off:
        # Strip off eighth bit
        # Translate NL to CR on input
        # Ignore carriage return on input
        # XON/XOFF flow control on output
        # (XSI) Typing any character will restart stopped output. NOTE: not needed?
        # XON/XOFF flow control on input
        iflag&= ~( ISTRIP | INLCR | IGNCR | ICRNL | IXON | IXANY | IXOFF )

        # turn off:
        # When any of the characters INTR, QUIT, SUSP, or DSUSP are received, generate the corresponding signal
        # canonical mode
        # Echo input characters (finally)
        # NOTE: why these three? they only work with ICANON and we're disabling it
        # If ICANON is also set, the ERASE character erases the preceding input character, and WERASE erases the preceding word
        # If ICANON is also set, the KILL character erases the current line
        # If ICANON is also set, echo the NL character even if ECHO is not set
        # implementation-defined input processing
        lflag&= ~( ISIG | ICANON | ECHO | ECHOE | ECHOK | ECHONL | IEXTEN )

        # turn off:
        # implementation-defined output processing
        oflag&= ~OPOST

        # NOTE: whatever
        # Minimum number of characters for noncanonical read
        cc[VMIN]= 1
        # Timeout in deciseconds for noncanonical read
        cc[VTIME]= 0

        tcsetattr(self.pairs[0][0], TCSADRAIN, [ iflag, oflag, cflag, lflag,
                                                 ispeed, ospeed, cc ])

    def read (self, src):
        if isinstance (src, io.IOBase):
            data= src.read (10240)
        elif isinstance (src, int):
            data= os.read (src, 10240)
        else:
            data= src.recv (10240)

        return data


    def write (self, dst, data):
        if isinstance (dst, io.IOBase):
            dst.write (data.decode ())
            dst.flush ()
        elif isinstance (dst, int):
            os.write (dst, data)
        else:
            dst.send (data)

    def fileno (self, f):
        if isinstance (f, int):
            return f
        elif getattr (f, 'fileno', None) is not None:
            return f.fileno ()
        else:
            raise TypeError (f)

    def run (self):
        # NOTE:
        # os.sendfile (self.dst, self.src, None, 0)
        # OSError: [Errno 22] Invalid argument
        # and splice() is not available
        # so, copy by hand
        while True:
            wait_for= list (self.copy_to.keys ())
            wait_for.append (self.finished[0])
            logger.debug (wait_for)
            for wait in wait_for:
                if ( not isinstance (wait, int) and
                     (getattr (wait, 'fileno', None) is None  or
                      not isinstance (wait.fileno(), int)) ):
                    logger.debug ('type mismatch: %s', wait)

            logger.debug (wait_for)
            r, w, e= select (wait_for, [], [])

            if self.finished[0] in r:
                self.close_file (self.finished[0])
                break

            for error in e:
                logger.debug ('%s error')
                # TODO: what?

            for i in r:
                o= self.copy_to[i]
                try:
                    data= self.read (i)
                    logger.debug ('%s -> %s: %s', i, o, data)

                # ValueError: read of closed file
                except (OSError, ValueError) as e:
                    logger.debug ('stopping copying for %s', i)
                    del self.copy_to[i]
                    logger.debug (traceback.format_exc ())
                    break
                else:
                    if len (data)==0:
                        logger.debug ('stopping copying for %s, no more data', i)
                        del self.copy_to[i]
                    else:
                        self.write (o, data)

        self.close ()
        logger.debug ('%s shutdown', self)


    def close (self):
        # reset term settings
        tcsetattr (self.pairs[0][0], TCSADRAIN, self.orig_terminfo)

        for k, v in self.pairs:
            for f in (k, v):
                if ( isinstance (f, paramiko.Channel) or
                     isinstance (f, io.TextIOWrapper) ):
                     self.close_file (f)

        self.close_file (self.finished[1])


    def close_file (self, f):
        logger.debug ('closing %s', f)
        try:
            try:
                f.close ()
            except AttributeError:
                # AttributeError: 'int' object has no attribute 'close'
                os.close (f)
        except OSError as e:
            logger.debug ('closing gave %s', e)
            if e.errno!=errno.EBADF:
                raise


class RemoteStub:
    def __init__ (self, pairs):
        self.interactive= InteractiveThread (pairs)
        self.interactive.start ()


    def close (self):
        self.interactive.close ()
        self.interactive.join ()


def clean_environment (d):
    return dict ([ (k, v) for k, v in d.items ()
                          if type (v)!=types.ModuleType
                             and k not in ('stdin', 'stdout', 'stderr',
                                           '__cffi_backend_extern_py',
                                           '__builtins__') ])

class remote:
    "Uses the same arguments as paramiko.SSHClient.connect ()"
    def __init__ (self, ast, hostname, *args, **kwargs):
        # actually, it's not a proper ast, it's the pickle of such thing
        self.ast= ast
        self.hostname= hostname
        self.args= args

        self.param ('_debug', kwargs)  # we're debugging, so we'll have lots of output
        self.param ('_test', kwargs)   # we're testing, so we'll use nc instead of ssh
        self.kwargs= kwargs
        # NOTE: uncomment to connect to the debugserver
        # self.kwargs['port']= 2244

        # socket/transport where we wait for connection for the result
        self.result_listen= None
        # socket/transport where the result is going to come back
        self.result_channel= None

        self.remote= None


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
        g= clean_environment (ayrton.runner.globals)

        # get the locals from the runtime
        # this is not so easy: for some reason, ayrton.runner.locals is not up to
        # date in the middle of the execution (remember *this* code is executed
        # via exec() in Ayrton.run_code())
        # another option is to go through the frames
        inception_locals= sys._getframe().f_back.f_locals
        l= clean_environment (inception_locals)

        # special treatment for argv
        g['argv']= ayrton.runner.globals['argv']

        logger.debug3 ('globals passed to remote: %s', ayrton.utils.dump_dict (g))
        global_env= pickle.dumps (g)
        logger.debug3 ('locals passed to remote: %s', ayrton.utils.dump_dict (l))
        local_env= pickle.dumps (l)

        backchannel_port= 4227

        # NOTE: becareful with the quoting here,
        # there are several levels at which they're interpreted:
        # 1) ayrton's local Python interpreter
        # 2) the remote shell
        # 3) the remote Python interpreter
        # in particular, getcwd()'s output MUST be between single quotes (')
        # so 2) does not think we're ending the double quotes (") around
        # the invocation of 3)
        # for the same reason, line #15 MUST have triple single quotes (''') too
        # and that's why the whole string MUST be in triple double quotes (""")
        if not self._debug and not self._test:
            precommand= ''
        else:
            precommand= '''import os; os.chdir ('%s')''' % os.getcwd ()
        logger.debug ("precommand: %s", precommand)

        command= """python3.5 -c "#!                                      #  1
import pickle                                                             #  2
# names needed for unpickling                                             #  3
from ast import Module, Assign, Name, Store, Call, Load, Expr             #  4
import sys                                                                #  5
from socket import socket                                                 #  6
import traceback                                                          #  7
                                                                          #  8
import logging                                                            #  9
logger= logging.getLogger ('ayrton.remote.runner')                        # 10
                                                                          # 11
# precommand, used by tests to change to the proper directory             # 12
# so it picks up the current version of the code.                         # 13
logger.debug ('precommand: %%s', '''%s''')                                # 14
%s                                                                        # 15
import ayrton #  this means that ayrton has to be installed in the remote # 16
                                                                          # 17
client= socket ()                                                         # 18
client.connect (('127.0.0.1', %d))                                        # 19
ast= pickle.loads (client.recv (%d))                                      # 20
logger.debug ('code to run:\\n%%s', ayrton.ast_pprinter.pprint (ast))     # 21
g= pickle.loads (client.recv (%d))                                        # 22
logger.debug2 ('globals received: %%s', ayrton.utils.dump_dict (g))       # 23
l= pickle.loads (client.recv (%d))                                        # 24
logger.debug2 ('locals received: %%s', ayrton.utils.dump_dict (l))        # 25
                                                                          # 26
# set the global runner so functions and Commands work                    # 27
ayrton.runner= ayrton.Ayrton (g, l)                                       # 28
caught= None                                                              # 29
result= None                                                              # 30
                                                                          # 31
try:                                                                      # 32
    result= ayrton.runner.run_tree (ast, 'from_remote')                   # 33
except Exception as e:                                                    # 34
    logger.debug ('run raised: %%r', e)                                   # 35
    logger.debug (traceback.format_exc())                                 # 36
    caught= e                                                             # 37
                                                                          # 38
logger.debug2 ('runner.locals: %%s', ayrton.utils.dump_dict (ayrton.runner.locals)) # 39
                                                                          # 40
logger.debug ('about to send exit status')                                # 41
data = pickle.dumps ( (ayrton.runner.locals, result, caught) )            # 42
logger.debug ('sending %%d bytes', len (data))                            # 43
client.sendall (data)                                                     # 44
logger.debug ('exit status sent')                                         # 45
client.close ()                                                           # 46"
""" % (precommand, precommand, backchannel_port,
       len (self.ast), len (global_env), len (local_env))

        logger.debug ('code to execute remote: %s', command)

        if not self._debug:
            self.client= paramiko.SSHClient ()
            # TODO: TypeError: invalid file: ['/home/mdione/.ssh/known_hosts']
            # self.client.load_host_keys (bash ('~/.ssh/known_hosts'))
            # self.client.set_missing_host_key_policy (ShutUpPolicy ())
            self.client.set_missing_host_key_policy (paramiko.WarningPolicy ())
            logger.debug ('connecting...')
            self.client.connect (self.hostname, *self.args, **self.kwargs)

            # create the backchannel
            # this channel will be used for sending/receiving runtime data
            # to/from the remote
            # the remote code will connect to it (line #18)
            # read the ast (#19), globals (#21) and locals (#23)
            # and return the locals, result and exception (#43)
            # the remote will see this channel as a localhost port
            # and it's seen on the local side as self.con defined below
            self.result_listen= self.client.get_transport ()
            logger.debug ('setting backchannel_port...')
            self.result_listen.request_port_forward ('localhost', backchannel_port)

            # taken from paramiko/client.py:SSHClient.exec_command()
            channel= self.client.get_transport ().open_session ()
            # TODO:
            #19:44:54.953791 getsockopt(3, SOL_TCP, TCP_NODELAY, [0], [4]) = 0 <0.000016>
            #19:44:54.953852 setsockopt(3, SOL_TCP, TCP_NODELAY, [1], 4) = 0 <0.000014>

            try:
                # TODO signal handler for SIGWINCH
                term= shutil.get_terminal_size ()
                channel.get_pty (os.environ['TERM'], term.columns, term.lines)
            except OSError:
                channel.get_pty (os.environ['TERM'], )

            logger.debug ('exec!')
            channel.exec_command (command)
            i= o= e= channel

            logger.debug ('waiting for backchannel...')
            self.result_channel= self.result_listen.accept ()
        else:
            self.client= socket ()
            self.client.connect ((self.hostname, 2233)) # nc listening here, see DebugRemoteTests
            # unbuffered
            i= open (self.client.fileno (), 'wb', 0)
            o= open (self.client.fileno (), 'rb', 0)
            e= open (self.client.fileno (), 'rb', 0)

            self.result_listen= socket ()
            # self.result_listen.setsockopt (SO_REUSEADDR, )
            self.result_listen.bind (('', backchannel_port))
            self.result_listen.listen (1)

            # so bash does not hang waiting from more input
            command+= 'exit\n'
            i.write (command.encode ())

            (self.result_channel, addr)= self.result_listen.accept ()

        logger.debug ('sending ast, globals, locals')
        # TODO: compress?
        self.result_channel.sendall (self.ast)
        self.result_channel.sendall (global_env)
        self.result_channel.sendall (local_env)

        # TODO: handle _in, _out, _err
        self.remote= RemoteStub (( (os.dup (0), i), (o, os.dup (1)), (e, os.dup (2)) ))


    def __exit__ (self, *args):
        logger.debug (args)
        data= b''
        partial= self.result_channel.recv (8196)
        while len(partial)>0:
            data+= partial
            partial= self.result_channel.recv (8196)

        logger.debug ('recieved %d bytes', len (data))
        (l, result, e)= pickle.loads (data)
        logger.debug ('result from remote: %r', result)
        logger.debug3 ('locals returned from remote: %s', ayrton.utils.dump_dict (l))
        logger.debug ('closing %s', self.result_channel)
        self.result_channel.close ()

        logger.debug ('closing %s', self.result_listen)
        self.result_listen.close ()
        logger.debug ('closing %s', self.remote)
        self.remote.close ()

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

        if e is not None:
            logger.debug ('raised from remote: %r', e)
            # TODO: this makes the exception be as if raised from here
            raise e
