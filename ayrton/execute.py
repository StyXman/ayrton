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
import errno
from traceback import format_exc

import ayrton

import logging
logger= logging.getLogger ('ayrton.execute')

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

class CommandNotFound (NameError):
    def __init__ (self, name):
        self.name= name

    def __str__ (self):
        return "CommandNotFound or NameError: command %(name)s not found or name %(name)s is not defined" % self.__dict__

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

def isiterable (o):
    """Returns True if o is iterable but not str/bytes type."""
    # TODO: what about Mappings?
    return (    isinstance (o, Iterable) and
            not isinstance (o, (bytes, str)) )

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
        self.captured_lines= None

        self.child_pid= None


    def prepare_fds (self):
        if '_in' in self.options:
            i= self.options['_in']
            logger.debug ('_in: %r', i)

            # this condition is complex, but basically handles any type of input
            # that is not going to be handled later in client()
            if (     not isinstance (i, io.IOBase)      # file and such objects
                 and type (i) not in (int, str, bytes)  # fd's and file names
                 and i is not None                      # special value for /dev/null
                 and not isinstance (i, Command) ):     # Command's
                if self.options['_in_tty']:
                    # TODO: no support yet for input from file when _in_tty
                    # NOTE: os.openpty() returns (master, slave)
                    # but when writing master=w, slave=r
                    logger.debug ('_in: using tty')
                    (master, slave)= os.openpty ()
                    self.stdin_pipe= (slave, master)
                else:
                    logger.debug ("_in:%s creates a pipe()", type (i))
                    self.stdin_pipe= os.pipe ()
            elif isinstance (i, Command):
                if i.options.get ('_out', None)==Capture:
                    # if it's a captured command, create a pipe to feed the data
                    logger.debug ("_in::Command, _in._out==Capture creates a pipe()")
                    self.stdin_pipe= os.pipe ()
                elif i.options.get ('_out', None)==Pipe:
                    # if it's a piped command, use its pipe and hope it runs in the bg
                    logger.debug ("_in::Command uses the stdout_pipe")
                    self.stdin_pipe= i.stdout_pipe

        logger.debug ("stdin_pipe: %s", self.stdin_pipe)

        if '_out' in self.options:
            if self.options['_out']==Capture:
                if self.options['_out_tty']:
                    if self.options['_in_tty']:
                        # we use a copy of the pty created for the stdin
                        logger.debug ('duping tty form _in to _out')
                        self.stdout_pipe= (os.dup (self.stdin_pipe[1]),
                                           os.dup (self.stdin_pipe[0]))
                    else:
                        # this time the order is right
                        logger.debug ('_out: using tty')
                        (master, slave)= os.openpty ()
                        self.stdout_pipe= (master, slave)
                else:
                    logger.debug ("_out==Capture creates a pipe()")
                    self.stdout_pipe= os.pipe ()
            elif self.options['_out']==Pipe:
                # this pipe should be picked up by the outer Command
                logger.debug ("_out==Pipe creates a pipe()")
                self.stdout_pipe= os.pipe ()

        logger.debug ("stdout_pipe: %s", self.stdout_pipe)

        if '_err' in self.options:
            if self.options['_err']==Capture:
                # if stdout is also Capture'd, then use the same pipe
                if not '_out' in self.options or self.options['_out']!=Capture:
                    # if stdout is a tty, hook to that one
                    if self.options['_out_tty']:
                        logger.debug ('duping tty form _out to _err')
                        self.stderr_pipe= (os.dup (self.stdout_pipe[0]),
                                           os.dup (self.stdout_pipe[1]))
                    else:
                        logger.debug ("_err==Capture creates a pipe()")
                        self.stderr_pipe= os.pipe ()
            elif self.options['_err']==Pipe:
                # this pipe should be picked up by the outer Command
                logger.debug ("_err==Pipe creates a pipe()")
                self.stderr_pipe= os.pipe ()

        logger.debug ("stderr_pipe: %s", self.stderr_pipe)


    def child (self):
        # HACK: figure out why this call, which is equivalent to
        # the following code, does not work
        # ayrton.set_logging_handler (ayrton.pid_based_handler ())

        # replace the old handler only if there was one to begin with
        if len (logging.root.handlers)>0:
            # close them so we don't get ResourceWarnings
            for handler in logging.root.handlers:
                handler.close ()

            logging.root.handlers= [ ayrton.pid_based_handler () ]

        logger.debug ('child')

        ifile= ofile= efile= None  # these hold the IOBase object to close

        try:
            if '_in' in self.options:
                i= self.options['_in']

                if i is None:
                    # connect to /dev/null
                    # it's not /dev/zero, see man (4) zero
                    logger.debug ("_in==None redirects from /dev/null")
                    i= os.open (os.devnull, os.O_RDONLY)
                elif isinstance (i, io.IOBase):
                    # this does not work with file like objects
                    ifile= i
                    logger.debug ("_in::IOBase redirects %s -> 0 (stdin)", ifile)
                    i= i.fileno ()
                elif type (i) in (str, bytes):
                    file_name= i
                    i= os.open (i, os.O_RDONLY)
                    logger.debug ("_in::(str|bytes) redirects %d (%s) -> 0 (stdin)", i, file_name)

                if isinstance (i, int):
                    logger.debug ("_in::int redirects %d -> 0 (stdin)", i)
                    os.dup2 (i, 0)
                    if ifile is None:
                        logger.debug ('closing %d', i)
                        os.close (i)
                    else:
                        # closes both the IOBase file and its fh
                        logger.debug ('closing %s', ifile)
                        ifile.close ()
                else:
                    # use the pipe prepared by prepare_fds()
                    # including the case where _in::Command
                    logger.debug ("_in::%s, redirect stdin_pipe from prepare_fds() to stdin", type (i))
                    r, w= self.stdin_pipe
                    logger.debug ("_in: redirecting %d -> 0", r)
                    os.dup2 (r, 0)
                    logger.debug ('closing %d', r)
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
                    o= os.open (os.devnull, os.O_WRONLY) # no need to create it
                    logger.debug ("_out==None, redirects stdout 1 -> %d (%s)", o, os.devnull)
                elif isinstance (o, io.IOBase):
                    # this does not work with file like objects
                    ofile= o
                    logger.debug ("_out::IOBase, redirects stdout 1 -> %s", ofile)
                    o= o.fileno ()
                elif type (o) in (bytes, str):
                    file_name= o
                    o= os.open (o, os.O_WRONLY)
                    logger.debug ("_out::(str|bytes), redirects stdout 1 -> %d (%s)", o, file_name)

                if isinstance (o, int):
                    logger.debug ("_out::int, redirects stdout 1 -> %d", o)
                    os.dup2 (o, 1)
                    if ofile is None:
                        logger.debug ('closing %d', o)
                        os.close (o)
                    else:
                        # closes both the IOBase file and its fh
                        logger.debug ('closing %s', ofile)
                        ofile.close ()
                elif o==Capture or o==Pipe:
                    r, w= self.stdout_pipe
                    logger.debug ("_out::(Capture or Pipe), redirects stdout 1 -> %d", w)
                    os.dup2 (w, 1)
                    logger.debug ('closing %d', w)
                    os.close (w)
                    os.close (r)

            if '_err' in self.options:
                e= self.options['_err']
                if e is None:
                    # connect to /dev/null
                    e= os.open (os.devnull, os.O_WRONLY) # no need to create it
                    logger.debug ("_err==None, redirects stderr 2 -> %d (%s)", e, os.devnull)
                    # this will be continued later in the next if
                elif isinstance (e, io.IOBase):
                    # this does not work with file like objects
                    efile= e
                    logger.debug ("_err::IOBase, redirects stderr 2 -> %s", efile)
                    e= e.fileno ()
                elif type (e) in (bytes, str):
                    file_name= e
                    e= os.open (e, os.O_WRONLY)
                    logger.debug ("_err::(str|bytes), redirects stderr 2 -> %d (%s)", e, file_name)

                if isinstance (e, int):
                    logger.debug ("_err::int, redirects stderr 2 -> %d", e)
                    os.dup2 (e, 2)
                    if efile is None:
                        logger.debug ('closing %d', e)
                        os.close (e)
                    else:
                        # closes both the IOBase file and its fh
                        logger.debug ('closing %s', efile)
                        efile.close ()
                elif e==Capture:
                    if '_out' in self.options and self.options['_out']==Capture:
                        # send it to stdout
                        logger.debug ("_err::Capture and _out::Capture, redirects stderr 2 -> 1")
                        os.dup2 (1, 2)
                    else:
                        r, w= self.stderr_pipe
                        logger.debug ("_err::Capture, redirects stderr 2 -> %d", w)
                        os.dup2 (w, 2)
                        logger.debug ('closing %d', r)
                        os.close (r)
        except FileNotFoundError as e:
            logger.debug (e)
            # TODO: report something
            os._exit (1)

        # restore some signals
        for i in (signal.SIGPIPE, signal.SIGINT):
            signal.signal (i, signal.SIG_DFL)

        try:
            os.execvpe (self.exe, self.args, self.options['_env'])
        except FileNotFoundError as e:
            logger.debug (e)
            # TODO: report something
            os._exit (127)


    def prepare_args (self, cmd, args, kwargs):
        ans= [cmd]

        for arg in args:
            if isinstance (arg, o):
                self.prepare_arg (ans, arg.key, arg.value)
            else:
                if isiterable (arg):
                    # a sequence type that is not string like
                    for elem in arg:
                        ans.append (str (elem))
                else:
                    ans.append (str (arg))

        for k, v in kwargs.items ():
            self.prepare_arg (ans, k, v)

        return ans


    def prepare_arg (self, seq, name, value):
        if value!=False:
            if isiterable (value):
                for elem in value:
                    seq.append (name)
                    seq.append (str (elem))

            else:
                seq.append (name)

                # this is not the same as 'not value'
                # because value can have any, well, value of any kind
                if value!=True:
                    seq.append (str (value))
        else:
            # TODO: --no-option?
            pass

    def parent (self):
        logger.debug ('parent')

        if self.stdin_pipe is not None:
            # str -> write into the fd
            # list -> write each
            # file -> take fd
            i= self.options['_in']

            r, w= self.stdin_pipe
            logger.debug ('closing %d', r)
            os.close (r)

            if isinstance (i, Iterable) and (not isinstance (i, Command) or
                                             i.options.get ('_out', None)==Capture):
                # this includes file-like's and Capture'd Commands
                for e in i:
                    os.write (w, str (e).encode (encoding))
                    os.write (w, self.options['_end'])
            elif not isinstance (i, Command):
                os.write (w, str (i).encode (encoding))
                os.write (w, self.options['_end'])

            logger.debug ('closing %d', w)
            os.close (w)

        # TODO: The return status of a pipeline is the exit status of the last
        # command, unless the pipefail option is enabled. If pipefail is enabled,
        # the pipeline's return status is the value of the last (rightmost)
        # command to exit with a non-zero status, or zero if all commands exit
        # successfully.
        if not self.options['_bg']:
            if self.options.get ('_out', None)==Capture:
                # if we don't do this, a program with lots of output freezes
                # when its output buffer is full
                # on the other hand, this might take a lot of memory
                # but it's the same as in foo=$(long_output)
                self.prepare_capture_file ()
                self.captured_lines= self.capture_file.readlines ()

            self.wait ()
            # NOTE: uhm?
            ayrton.runner.wait_for_pending_children ()
        else:
            ayrton.runner.pending_children.append (self)


    def wait (self):
        logger.debug (self.child_pid)

        if self._exit_code is None:
            self._exit_code= os.waitpid (self.child_pid, 0)[1] >> 8

            if self._exit_code==127:
                # NOTE: when running bash, it returns 127 when it can't find the script to run
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

        # TODO: why this again here? see __init__()
        self._exit_code= None
        self.capture_file= None

        self.prepare_fds ()

        if type (self.options['_end'])!=bytes:
            self.options['_end']= str (self.options['_end']).encode (encoding)

        logger.debug ('fork')
        r= os.fork ()
        if r==0:
            try:
                self.child ()
            except Exception as e:
                logger.debug ('child borked')
                logger.debug (format_exc())

            # catch all
            os._exit (1)
        else:
            self.child_pid= r
            self.parent ()

        return self


    def __bool__ (self):
        if self._exit_code is None:
            self.wait ()
        return self._exit_code==0


    def prepare_capture_file (self):
        if self.capture_file is None:
            reader_pipe= None

            if self.stdout_pipe is not None:
                # this will also read stderr if both are Capture'd
                reader_pipe= self.stdout_pipe
            if self.stderr_pipe is not None:
                reader_pipe= self.stderr_pipe

            if reader_pipe is not None and self.options.get ('_out', None)!=Pipe:
                r, w= reader_pipe
                logger.debug ('closing %d', w)
                os.close (w)
                self.capture_file= open (r, encoding=encoding)


    def __str__ (self):
        self.wait ()

        if self.captured_lines:
            s= ''.join (self.captured_lines)
        else:
            self.prepare_capture_file ()
            s= self.capture_file.read ()

        return s


    def __iter__ (self):
        logger.debug ('iterating!')

        if self.captured_lines:
            for line in self.captured_lines:
                # while iterating we always remove the trailing \n
                line= line.rstrip (os.linesep)
                yield line
        else:
            self.prepare_capture_file ()

            for line in self.capture_file.readlines ():
                # while iterating we always remove the trailing \n
                line= line.rstrip (os.linesep)

                logger.debug2 ('read line: %s', line.encode(encoding))
                yield line

            # finish him!
            logger.debug ('finished!')
            self.capture_file.close ()
            # if we're iterating, then the Command is in _bg
            self.wait ()


    def readlines (self):
        self.wait ()

        if self.captured_lines:
            lines= self.captured_lines
        else:
            self.prepare_capture_file ()
            lines= self.capture_file.readlines ()
            self.capture_file.close ()

        return lines


    # BUG this method is leaking an opened file()
    # self.capture_file
    def readline (self):
        self.wait ()

        if self.captured_lines:
            line= self.captured_lines.pop (0)
        else:
            self.prepare_capture_file ()
            line= self.capture_file.readline ()

        if self.options['_chomp']:
            line= line.rstrip (os.linesep)

        return line


    def close (self):
        self.wait ()
        self.capture_file.close ()


    def __del__ (self):
        # finish it
        if self._exit_code is None and self.child_pid is not None:
            self.wait ()
