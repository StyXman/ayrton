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
    if '_in' in options and not isinstance (options['_in'], io.IOBase):
        stdin_pipe= os.pipe ()

    r= os.fork ()
    if r==0:
        # child
        if '_in' in options:
            i= options['_in']
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
            if isinstance (o, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stdout (1)
                os.dup2 (o.fileno (), 1)

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

        return os.wait ()

if __name__=='__main__':
    a= execute ('echo', 'yes!')

    a= execute ('echo', 42)

    a= execute ('cat', _in='yes!')

    f= open ('ayrton/tests/string_stdin.txt', 'rb')
    a= execute ('cat', _in=f)
    f.close ()

    a= execute ('cat', _in=['a', 'b'])

    f= open ('ayrton/tests/string_stdout.txt', 'wb+')
    a= execute ('echo', 'yes!', _out=f)
    f.close ()

    a= execute ('cat', _in=None)
