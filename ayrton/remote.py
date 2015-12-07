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

import logging
logger= logging.getLogger ('ayrton.remote')

class ShutUpPolicy (paramiko.MissingHostKeyPolicy):
    def missing_host_key (self, *args, **kwargs):
        pass

# TODO:
#19:44:54.884213 ioctl(5, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000015>
#19:44:54.884267 ioctl(6, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000014>
#19:44:54.884316 ioctl(7, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000013>
#19:44:54.884369 fcntl(5, F_SETFD, FD_CLOEXEC) = 0 <0.000013>
#19:44:54.884415 fcntl(6, F_SETFD, FD_CLOEXEC) = 0 <0.000013>
#19:44:54.884459 fcntl(7, F_SETFD, FD_CLOEXEC) = 0 <0.000013>
#19:44:54.885998 ioctl(0, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000021>
#19:44:54.886083 ioctl(0, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000014>
#19:44:54.886137 ioctl(0, SNDCTL_TMR_STOP or TCSETSW, {B38400 -opost -isig -icanon -echo ...}) = 0 <0.000016>
#19:44:54.886190 ioctl(0, TCGETS, {B38400 -opost -isig -icanon -echo ...}) = 0 <0.000013>

#19:44:54.953791 getsockopt(3, SOL_TCP, TCP_NODELAY, [0], [4]) = 0 <0.000016>
#19:44:54.953852 setsockopt(3, SOL_TCP, TCP_NODELAY, [1], 4) = 0 <0.000014>

#19:44:54.955976 select(8, [3 5], [], NULL, NULL) = 1 (in [3]) <0.000016>
#19:44:54.956074 read(3, "o\266@g\334F2\236/J\3768\347]\345\265<\331\336\32\210)\250\3261\214\376kZ\326h\2674K\27T\263d\34\314\315\264S0\352A\301\335y\305\377R\345B]\360\322 \200h5\244\366U\32197\250\273\314\353\4\357\214K\261\350\323\342\343\27I\25\v\314\244G|\22\333\256\262\274v\211\313\30u\344D\320\276\241\256u\302\267\"\3607w\3320\2403]\0345\34Ch%@(\37\367\376\255"..., 8192) = 520 <0.000033>
#19:44:54.956288 select(8, [3 5], [6], NULL, NULL) = 1 (out [6]) <0.000017>
#19:44:54.956399 write(6, "\r\nThe programs included with the Debian GNU/Linux system are free software;\r\nthe exact distribution terms for each program are d"..., 367) = 367 <0.000018>
#19:44:54.956583 select(8, [3 5], [], NULL, NULL) = 1 (in [3]) <0.113194>
#19:44:55.069989 read(3, "\234\27\263\30i\262\305\336\361\f\16\374,9\251;\225h\236\262\26\343\213I-\300]f\206\266D\263\337+\36\356=\216\r\335\257.Y\203\327\347\314\265\245mUP\311Z\3\230\242{s5\0\216\342\225\1\353\303_\202\25\347\353\236\305\207R", 8192) = 76 <0.000069>
#19:44:55.070305 select(8, [3 5], [6], NULL, NULL) = 1 (out [6]) <0.000009>
#19:44:55.070407 write(6, "\33]0;mdione@diablo: ~\7mdione@diablo:~$ ", 38) = 38 <0.000027>
#19:44:55.070528 select(8, [3 5], [], NULL, NULL) = 1 (in [5]) <3.407809>
#19:44:58.478516 read(5, "\4", 16384)    = 1 <0.000020>
#19:44:58.479153 select(8, [3 5], [], NULL, NULL) = 1 (in [3]) <0.000129>
#19:44:58.479421 read(3, "D\332\236-\331\26b\214\214%C3*U\243\2412)\240\241\354\303X\251\273\246\203\316\361l\304q\37\264\353\205\202\301\2\364\254m\214W", 8192) = 44 <0.000018>
#19:44:58.479607 select(8, [3 5], [6], NULL, NULL) = 1 (out [6]) <0.000015>
#19:44:58.479708 write(6, "logout\r\n", 8) = 8 <0.000017>

#19:44:58.483894 close(5)                = 0 <0.000015>
#19:44:58.483956 close(6)                = 0 <0.000015>
#19:44:58.484011 clock_gettime(CLOCK_BOOTTIME, {1233289, 294825737}) = 0 <0.000014>
#19:44:58.484063 clock_gettime(CLOCK_BOOTTIME, {1233289, 294876787}) = 0 <0.000014>
#19:44:58.484115 ioctl(0, TCGETS, {B38400 -opost -isig -icanon -echo ...}) = 0 <0.000015>
#19:44:58.484170 ioctl(0, SNDCTL_TMR_STOP or TCSETSW, {B38400 opost isig icanon echo ...}) = 0 <0.000018>
#19:44:58.484228 ioctl(0, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000015>
#19:44:58.484300 close(7)                = 0 <0.000015>
#19:44:58.484746 ioctl(0, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000015>
#19:44:58.484800 ioctl(1, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000015>
#19:44:58.484853 ioctl(2, TCGETS, {B38400 opost isig icanon echo ...}) = 0 <0.000015>
#19:44:58.484908 write(2, "Connection to localhost closed.\r\n", 33) = 33 <0.000023>


class InteractiveThread (Thread):
    def __init__ (self, pairs):
        super ().__init__ ()
        # so I can close them at will
        logger.debug ('%s: %s', self, pairs)
        self.pairs= pairs
        self.finished= os.pipe ()


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
            wait_for= list (self.pairs.keys ())
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
                o= self.pairs[i]
                try:
                    data= self.read (i)
                    logger.debug ('%s -> %s: %s', i, o, data)

                # ValueError: read of closed file
                except (OSError, ValueError) as e:
                    logger.debug ('stopping copying for %s', i)
                    del self.pairs[i]
                    logger.debug (traceback.format_exc ())
                    break
                else:
                    if len (data)==0:
                        logger.debug ('stopping copying for %s, no more data', i)
                        del self.pairs[i]
                    else:
                        self.write (o, data)

        self.close ()
        logger.debug ('%s shutdown', self)


    def close (self):
        for k, v in list (self.pairs.items ()):
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


class remote:
    "Uses the same arguments as paramiko.SSHClient.connect ()"
    def __init__ (self, ast, hostname, *args, **kwargs):
        # actually, it's not a proper ast, it's the pickle of such thing
        self.ast= ast
        self.hostname= hostname
        self.args= args

        self.param ('_debug', kwargs)
        self.param ('_test', kwargs)
        self.kwargs= kwargs

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
            self.result_listen= self.client.get_transport ()
            self.result_listen.request_port_forward ('localhost', port)

            (i, o, e)= self.client.exec_command (command, get_pty=True)
            if isinstance (i, paramiko.ChannelFile):
                # I don't expect mixed files
                # so select() works on them
                i= i.channel
                o= o.channel
                e= e.channel

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
            self.result_listen.bind (('', port))
            self.result_listen.listen (1)

            # so bash does not hang waiting from more input
            command+= 'exit\n'
            i.write (command.encode ())

            (self.result_channel, addr)= self.result_listen.accept ()

        logger.debug ('sending ast, globals, locals')
        self.result_channel.sendall (self.ast)
        self.result_channel.sendall (global_env)
        self.result_channel.sendall (local_env)

        # TODO: handle _in, _out, _err
        self.remote= RemoteStub ({os.dup (0): i, o: os.dup (1), e: os.dup (2)})


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
