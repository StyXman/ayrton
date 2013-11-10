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
from ayrton import Capture

# encoding= 'utf-8'
encoding= sys.getdefaultencoding ()

def execute (cmd, *args, **kwargs):
    options= dict (
        _end= os.linesep.encode (encoding),
        )
    options.update (kwargs)

    if type (options['_end'])!=bytes:
        options['_end']= options['_end'].encode (encoding)

    stdin_pipe= None
    if '_in' in options:
        i= options['_in']
        if not isinstance (i, io.IOBase) and i is not None:
            stdin_pipe= os.pipe ()

    stdout_pipe= None
    if '_out' in options and options['_out']==Capture:
        stdout_pipe= os.pipe ()

    r= os.fork ()
    if r==0:
        # child
        if '_in' in options:
            i= options['_in']
            if i is None:
                # connect to /dev/null
                # it's not /dev/zero, see man (4) zero
                i= open (os.devnull, 'rb')

            if isinstance (i, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stdin (0)
                os.dup2 (i.fileno (), 0)
            else:
                r, w= stdin_pipe
                os.dup2 (r, 0)
                os.close (w)

        if '_out' in options:
            o= options['_out']
            if o is None:
                # connect to /dev/null
                o= open (os.devnull, 'wb') # no need to create it

            if isinstance (o, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stdout (1)
                os.dup2 (o.fileno (), 1)

            if o==Capture:
                r, w= stdout_pipe
                os.dup2 (w, 1)
                os.close (r)

        if '_err' in options:
            e= options['_err']
            if e is None:
                # connect to /dev/null
                e= open (os.devnull, 'wb') # no need to create it

            if isinstance (e, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stderr (2)
                os.dup2 (e.fileno (), 2)

            if e==Capture:
                if '_out' in options and options['_out']==Capture:
                    # send it to the same pipe as stdout
                    r, w= stdout_pipe
                    os.dup2 (w, 2)
                else:
                    r, w= stderr_pipe
                    os.dup2 (w, 2)
                    os.close (r)

        os.execvp (cmd, [cmd]+[str (x) for x in args])
    else:
        # parent, r is the pid of the child
        if stdin_pipe is not None:
            # str -> write into the fd
            # list -> write each
            # file -> take fd
            i= options['_in']

            r, w= stdin_pipe
            os.close (r)

            if type (i)==str:
                os.write (w, i.encode (encoding))
                os.write (w, options['_end'])
            elif type (i)==bytes:
                os.write (w, i)
                os.write (w, options['_end'])
            elif isinstance (i, Iterable):
                for e in i:
                    os.write (w, str (e).encode (encoding))
                    os.write (w, options['_end'])
            else:
                os.write (w, str (i).encode (encoding))
                os.write (w, options['_end'])

            os.close (w)

        ans= os.wait ()

        if stdout_pipe is not None:
            r, w= stdout_pipe
            os.close (w)
            ans= os.read (r, 1024).decode (encoding)
            os.close (r)

        return ans

if __name__=='__main__':
    a= execute ('echo', 'simple')

    a= execute ('echo', 42)

    a= execute ('cat', _in='_in=str')

    a= execute ('cat', _in=b'_in=bytes')

    f= open ('ayrton/tests/data/string_stdin.txt', 'rb')
    a= execute ('cat', _in=f)
    f.close ()

    a= execute ('cat', _in=['sequence', 'test'])

    f= open ('ayrton/tests/data/string_stdout.txt', 'wb+')
    a= execute ('echo', 'stdout_to_file', _out=f)
    f.close ()

    a= execute ('cat', _in=None)

    a= execute ('echo', '_out=None', _out=None)

    a= execute ('echo', 'Capture', _out=Capture)
    print (repr (a))

    f= open ('ayrton/tests/data/string_stderr.txt', 'wb+')
    a= execute ('ls', 'stderr_to_file', _err=f)
    f.close ()
