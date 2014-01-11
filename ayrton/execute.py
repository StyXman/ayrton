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
import ayrton

encoding= sys.getdefaultencoding ()

# special value to signal that the output should be captured
# instead of going to stdout
Capture= (42, )

class o (object):
    def __init__ (self, **kwargs):
        option= list (kwargs.items ())[0]
        self.key=   option[0]
        self.value= option[1]

class CommandFailed (Exception):
    def __init__ (self, code):
        self.code= code

class CommandNotFound (Exception):
    def __init__ (self, path):
        self.path= path

class Command:
    default_options= dict (
        _in_tty= False,
        _out_tty= False,
        _env= {},
        _end= os.linesep.encode (encoding),
        _chomp= True,
        _encoding= encoding,
        )

    supported_options= ('_in', '_out', '_err', '_end', '_chomp', '_encoding',
                        '_env',)

    def __init__ (self, path):
        self.path= path

        self.stdin_pipe= None
        self.stdout_pipe= None
        self.stderr_pipe= None

        self.exit_code= None
        self.capture_file= None

    def prepare_fds (self):
        if '_in' in self.options:
            i= self.options['_in']
            if not isinstance (i, io.IOBase) and type (i)!=int and i is not None:
                if self.options['_in_tty']:
                    # TODO: no support yet for input from file when _in_tty
                    # NOTE: os.openpty() returns (master, slave)
                    # but when writing master=w, slave=r
                    (master, slave)= os.openpty ()
                    self.stdin_pipe= (slave, master)
                else:
                    self.stdin_pipe= os.pipe ()

        if '_out' in self.options and self.options['_out']==Capture:
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
                self.stdout_pipe= os.pipe ()

        if '_err' in self.options and self.options['_err']==Capture:
            # if stdout is also Capture'd, then use the same pipe
            if not '_out' in self.options or self.options['_out']!=Capture:
                # if stdout is a tty, hook to that one
                if self.options['_out_tty']:
                    self.stderr_pipe= (os.dup (self.stdout_pipe[0]),
                                       os.dup (self.stdout_pipe[1]))
                else:
                    self.stderr_pipe= os.pipe ()

    def child (self, cmd, *args, **kwargs):
        if '_in' in self.options:
            i= self.options['_in']
            if i is None:
                # connect to /dev/null
                # it's not /dev/zero, see man (4) zero
                i= open (os.devnull, 'rb')

            if isinstance (i, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stdin (0)
                os.dup2 (i.fileno (), 0)
            elif type (i)==int:
                os.dup2 (i, 0)
            else:
                r, w= self.stdin_pipe
                os.dup2 (r, 0)
                os.close (w)

        if '_out' in self.options:
            o= self.options['_out']
            if o is None:
                # connect to /dev/null
                o= open (os.devnull, 'wb') # no need to create it

            if isinstance (o, io.IOBase):
                # this does not work with file like objects
                # dup its fd in stdout (1)
                os.dup2 (o.fileno (), 1)
            elif type (o)==int:
                os.dup2 (o, 1)
            elif o==Capture:
                r, w= self.stdout_pipe
                os.dup2 (w, 1)
                os.close (r)
            elif type (o) in (bytes, str):
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
                    # send it to the same pipe as stdout
                    r, w= self.stdout_pipe
                    os.dup2 (w, 2)
                else:
                    r, w= self.stderr_pipe
                    os.dup2 (w, 2)
                    os.close (r)

        # args is a tuple
        args= self.prepare_args (cmd, args, kwargs)
        try:
            os.execvpe (cmd, args, self.options['_env'])
        except FileNotFoundError:
            os._exit (127)

    def prepare_args (self, cmd, args, kwargs):
        ans= [cmd]

        for arg in args:
            if type (arg)==o:
                self.prepare_arg (ans, arg.key, arg.value)
            else:
                ans.append (arg)

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

    def parent (self, cmd, child_pid):
        reader_pipe= None

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
            elif isinstance (i, Iterable):
                for e in i:
                    os.write (w, str (e).encode (encoding))
                    os.write (w, self.options['_end'])
            else:
                os.write (w, str (i).encode (encoding))
                os.write (w, self.options['_end'])

            os.close (w)

        self.exit_code= os.waitpid (child_pid, 0)[1] >> 8

        if self.stdout_pipe is not None:
            # this will also read stderr if both are Capture'd
            reader_pipe= self.stdout_pipe
        if self.stderr_pipe is not None:
            reader_pipe= self.stderr_pipe

        if reader_pipe is not None:
            r, w= reader_pipe
            os.close (w)
            self.capture_file= open (r)

        if self.exit_code==127:
            raise CommandNotFound (cmd)

        if ayrton.runner.options.get ('errexit', False) and self.exit_code!=0:
            raise CommandFailed (self)

    def __call__ (self, *args, **kwargs):
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

        self.options['_env'].update (ayrton.runner.environ.os_environ)

        self.stdin_pipe= None
        self.stdout_pipe= None
        self.stderr_pipe= None

        self.exit_code= None
        self.capture_file= None

        self.prepare_fds ()

        if type (self.options['_end'])!=bytes:
            self.options['_end']= str (self.options['_end']).encode (encoding)

        r= os.fork ()
        if r==0:
            self.child (self.path, *args, **kwargs)
        else:
            self.parent (self.path, r)

        return self

    def __bool__ (self):
        return self.exit_code==0

    def __str__ (self):
        return self.capture_file.read ()

    def __iter__ (self):
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
        line= self.capture_file.readline ()
        if self.options['_chomp']:
            line= line.rstrip (os.linesep)

        return line

    def close (self):
        self.capture_file.close ()

    def readlines (self):
        # ugly way to not leak the file()
        return ( line for line in self )
