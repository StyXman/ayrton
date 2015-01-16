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
import io
from collections.abc import Iterable
import signal

# import logging

# logging.basicConfig(filename='tmp/bar.log',level=logging.DEBUG)

import ayrton

encoding= sys.getdefaultencoding ()

# special value to signal that the output should be captured
# instead of going to stdout
class Capture:
    pass

# same, but for a pipe
class Pipe:
    pass

class o (object):
    def __init__ (self, **kwargs):
        option= list (kwargs.items ())[0]
        self.key=   option[0]
        self.value= option[1]

class CommandFailed (Exception):
    def __init__ (self, command):
        self.command= command

    def __str__ (self):
        return "%s: %d" % (' '.join ([ repr (arg) for arg in self.command.args]), self.command._exit_code)

class CommandNotFound (Exception):
    def __init__ (self, path):
        self.path= path

def which(program):
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program

    else:
        if "PATH" not in os.environ:
            return None

        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def resolve_program(program):
    path = which(program)
    if not path:
        # our actual command might have a dash in it, but we can't call
        # that from python (we have to use underscores), so we'll check
        # if a dash version of our underscore command exists and use that
        # if it does
        if "_" in program:
            path = which(program.replace("_", "-"))

        if not path:
            return None

    return path

class Command:
    default_options= dict (
        _in_tty= False,
        _out_tty= False,
        _env= {},
        _end= os.linesep.encode (encoding),
        _chomp= True,
        _encoding= encoding,
        _bg= False,
        _fails= False,
        )

    supported_options= ('_in', '_out', '_err', '_end', '_chomp', '_encoding',
                        '_env', '_bg', '_fails')

    def __init__ (self, path):
        self.path= path
        self.exe= resolve_program (path)
        self.command= None

        self.stdin_pipe= None
        self.stdout_pipe= None
        self.stderr_pipe= None

        self._exit_code= None
        self.capture_file= None

        self.child_pid= None

    def prepare_fds (self):
        if '_in' in self.options:
            i= self.options['_in']
            if ( not isinstance (i, io.IOBase) and
                 type (i)!=int and
                 i is not None and
                 not isinstance (i, Command) ):
                if self.options['_in_tty']:
                    # TODO: no support yet for input from file when _in_tty
                    # NOTE: os.openpty() returns (master, slave)
                    # but when writing master=w, slave=r
                    (master, slave)= os.openpty ()
                    self.stdin_pipe= (slave, master)
                else:
                    # logging.debug ("prepare_fds: _in::%s creates a pipe()", type (i))
                    self.stdin_pipe= os.pipe ()
            elif isinstance (i, Command):
                if i.options.get ('_out', None)==Capture:
                    # if it's a captured command, create a pipe to feed the data
                    # logging.debug ("prepare_fds: _in::Command, _in._out==Capture creates a pipe()")
                    self.stdin_pipe= os.pipe ()
                elif i.options.get ('_out', None)==Pipe:
                    # if it's a piped command, use its pipe and hope it runs in the bg
                    # logging.debug ("prepare_fds: _in::Command uses the stdout_pipe")
                    self.stdin_pipe= i.stdout_pipe

        if '_out' in self.options:
            if self.options['_out']==Capture:
                if self.options['_out_tty']:
                    if self.options['_in_tty']:
                        # we use a copy of the pty created for the stdin
                        self.stdout_pipe= (os.dup (self.stdin_pipe[1]),
                                           os.dup (self.stdin_pipe[0]))
                    else:
                        # this time the order is right
                        (master, slave)= os.openpty ()
                        self.stdout_pipe= (master, slave)
                else:
                    # logging.debug ("prepare_fds: _out==Capture creates a pipe()")
                    self.stdout_pipe= os.pipe ()
            elif self.options['_out']==Pipe:
                # this pipe should be picked up by the outer Command
                # logging.debug ("prepare_fds: _out==Pipe creates a pipe()")
                self.stdout_pipe= os.pipe ()

        if '_err' in self.options:
            if self.options['_err']==Capture:
                # if stdout is also Capture'd, then use the same pipe
                if not '_out' in self.options or self.options['_out']!=Capture:
                    # if stdout is a tty, hook to that one
                    if self.options['_out_tty']:
                        self.stderr_pipe= (os.dup (self.stdout_pipe[0]),
                                           os.dup (self.stdout_pipe[1]))
                    else:
                        # logging.debug ("prepare_fds: _err==Capture creates a pipe()")
                        self.stderr_pipe= os.pipe ()
            elif self.options['_err']==Pipe:
                # this pipe should be picked up by the outer Command
                # logging.debug ("prepare_fds: _err==Pipe creates a pipe()")
                self.stderr_pipe= os.pipe ()

    def child (self):
        if '_in' in self.options:
            i= self.options['_in']
            if i is None:
                # connect to /dev/null
                # it's not /dev/zero, see man (4) zero
                i= open (os.devnull, 'rb')

            if isinstance (i, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stdin (0)
                # logging.debug ("child: _in::IOBase redirects file to stdin")
                os.dup2 (i.fileno (), 0)
                i.close ()
            elif type (i)==int:
                # logging.debug ("child: _in::int redirects fd to stdin")
                os.dup2 (i, 0)
                os.close (i)
            else:
                # use the pipe prepared by prepare_fds()
                # including the case where _in::Command
                # logging.debug ("child: _in::%s, redirect stdin_pipe from prepare_fds() to stdin", type (i))
                r, w= self.stdin_pipe
                os.dup2 (r, 0)
                os.close (r)
                # the write fd can already be closed in this case:
                # a= cat (..., _out=capture)
                # b= grep (..., _in= a)
                # once a's lines have been read, t
                os.close (w)

        if '_out' in self.options:
            o= self.options['_out']
            if o is None:
                # connect to /dev/null
                o= open (os.devnull, 'wb') # no need to create it

            if isinstance (o, io.IOBase):
                # this does not work with file like objects
                # dup its fd in stdout (1)
                # logging.debug ("child: _out::IOBase, redirects stout to file")
                os.dup2 (o.fileno (), 1)
                o.close ()
            elif type (o)==int:
                # logging.debug ("child: _out::int, redirects stdout to fd")
                os.dup2 (o, 1)
                os.close (o)
            elif o==Capture or o==Pipe:
                # logging.debug ("child: _out::(Capture or Pipe), stdout -> stdout_pipe")
                r, w= self.stdout_pipe
                os.dup2 (w, 1)
                os.close (w)
                os.close (r)
            elif type (o) in (bytes, str):
                # BUG: this is inconsistent with _in::str
                # logging.debug ("child: _out::str, open file and redirect ")
                f= open (o, 'w+')
                os.dup2 (f.fileno (), 1)
                f.close ()

        if '_err' in self.options:
            e= self.options['_err']
            if e is None:
                # connect to /dev/null
                e= open (os.devnull, 'wb') # no need to create it

            if isinstance (e, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stderr (2)
                os.dup2 (e.fileno (), 2)

            if e==Capture:
                if '_out' in self.options and self.options['_out']==Capture:
                    # send it to stdout
                    os.dup2 (1, 2)
                else:
                    r, w= self.stderr_pipe
                    os.dup2 (w, 2)
                    os.close (r)

        # restore some signals
        for i in (signal.SIGPIPE, ):
            signal.signal (i, signal.SIG_DFL)

        try:
            os.execvpe (self.exe, self.args, self.options['_env'])
        except FileNotFoundError:
            os._exit (127)

    def prepare_args (self, cmd, args, kwargs):
        ans= [cmd]

        for arg in args:
            if type (arg)==o:
                self.prepare_arg (ans, arg.key, arg.value)
            else:
                ans.append (str (arg))

        for k, v in kwargs.items ():
            self.prepare_arg (ans, k, v)

        return ans

    def prepare_arg (self, seq, name, value):
        if value!=False:
            if len (name)==1:
                arg="-%s" % name
            else:
                # TODO: longopt_prefix
                # and/or simply subclass find(Command)
                arg="--%s" % name
            seq.append (arg)

            if value!=True:
                seq.append (str (value))

    def parent (self):
        if self.stdin_pipe is not None:
            # str -> write into the fd
            # list -> write each
            # file -> take fd
            i= self.options['_in']

            r, w= self.stdin_pipe
            os.close (r)

            if type (i)==str:
                os.write (w, i.encode (encoding))
                os.write (w, self.options['_end'])
            elif type (i)==bytes:
                os.write (w, i)
                os.write (w, self.options['_end'])
            elif isinstance (i, Iterable) and (not isinstance (i, Command) or
                                               i.options.get ('_out', None)==Capture):
                # this includes file-like's and Capture'd Commands
                for e in i:
                    os.write (w, str (e).encode (encoding))
                    os.write (w, self.options['_end'])
            elif not isinstance (i, Command):
                os.write (w, str (i).encode (encoding))
                os.write (w, self.options['_end'])

            os.close (w)

        # TODO: The return status of a pipeline is the exit status of the last
        # command, unless the pipefail option is enabled.  If pipefail is enabled,
        # the pipeline's return status  is  the value  of the last (rightmost)
        # command to exit with a non-zero status, or zero if all commands exit
        # successfully.
        if not self.options['_bg']:
            self.wait ()
            ayrton.runner.wait_for_pending_children ()
        else:
            ayrton.runner.pending_children.append (self)

    def wait (self):
        self._exit_code= os.waitpid (self.child_pid, 0)[1] >> 8

        reader_pipe= None

        if self.stdout_pipe is not None:
            # this will also read stderr if both are Capture'd
            reader_pipe= self.stdout_pipe
        if self.stderr_pipe is not None:
            reader_pipe= self.stderr_pipe

        if reader_pipe is not None and self.options.get ('_out', None)!=Pipe:
            r, w= reader_pipe
            os.close (w)
            self.capture_file= open (r)

        if self._exit_code==127:
            raise CommandNotFound (self.path)

        if (ayrton.runner.options.get ('errexit', False) and
            self._exit_code!=0 and
            not self.options.get ('_fails', False)):

            raise CommandFailed (self)

    def exit_code (self):
        if self._exit_code is None:
            self.wait ()
        return self._exit_code

    def __call__ (self, *args, **kwargs):
        if self.exe is None:
            raise CommandNotFound (self.path)

        self.options= self.default_options.copy ()
        for option in self.supported_options:
            try:
                # update with the passed value
                self.options[option]= kwargs[option]
                # we don't need the option anymore
                del kwargs[option]
            except KeyError:
                # ignore
                pass

        self.options['_env'].update (os.environ)
        self.args= self.prepare_args (self.exe, args, kwargs)

        self.stdin_pipe= None
        self.stdout_pipe= None
        self.stderr_pipe= None

        self._exit_code= None
        self.capture_file= None

        self.prepare_fds ()

        if type (self.options['_end'])!=bytes:
            self.options['_end']= str (self.options['_end']).encode (encoding)

        r= os.fork ()
        if r==0:
            self.child ()
        else:
            self.child_pid= r
            self.parent ()

        return self

    def __bool__ (self):
        if self._exit_code is None:
            self.wait ()
        return self._exit_code==0

    def __str__ (self):
        if self._exit_code is None:
            self.wait ()
        return self.capture_file.read ()

    def __iter__ (self):
        if self._exit_code is None:
            self.wait ()
        if self.capture_file is not None:
            for line in self.capture_file.readlines ():
                if self.options['_chomp']:
                    line= line.rstrip (os.linesep)

                yield line

            # finish him!
            self.capture_file.close ()
        else:
            # TODO
            pass

    # BUG this method is leaking an opend file()
    # self.capture_file
    def readline (self):
        if self._exit_code is None:
            self.wait ()
        line= self.capture_file.readline ()
        if self.options['_chomp']:
            line= line.rstrip (os.linesep)

        return line

    def close (self):
        if self._exit_code is None:
            self.wait ()
        self.capture_file.close ()

    def readlines (self):
        if self._exit_code is None:
            self.wait ()
        # ugly way to not leak the file()
        return ( line for line in self )

    def __del__ (self):
        # finish it
        if self._exit_code is None and self.child_pid is not None:
            self.wait ()
