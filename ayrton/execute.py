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
    stdin_pipe= None
    if '_in' in kwargs and not isinstance (kwargs['_in'], io.IOBase):
        stdin_pipe= os.pipe ()

    r= os.fork ()
    if r==0:
        # child
        if '_in' in kwargs:
            i= kwargs['_in']
            if isinstance (i, io.IOBase):
                # this does not work with file like objects
                # dup its fd int stdin (0)
                os.dup2 (i.fileno (), 0)
            else:
                r, w= stdin_pipe
                os.dup2 (r, 0)
                os.close (w)

        if '_out' in kwargs:
            o= kwargs['_out']

        os.execvp (cmd, [cmd]+[str (x) for x in args])
    else:
        # parent, r is the pid of the child
        if stdin_pipe is not None:
            # str -> write into the fd
            # list -> write each
            # file -> take fd
            i= kwargs['_in']

            r, w= stdin_pipe
            os.close (r)

            if type (i)==str:
                os.write (w, i.encode (encoding))
            elif type (i)==bytes:
                os.write (w, i)
            elif isinstance (i, Iterable):
                for e in i:
                    os.write (w, str (e).encode (encoding))
            else:
                os.write (w, str (i).encode (encoding))

            os.close (w)

        return os.wait ()

if __name__=='__main__':
    a= execute ('echo', 'yes!')

    a= execute ('echo', 42)

    a= execute ('cat', _in='yes!')

    f= open ('ayrton/tests/string_stdin.txt', 'rb')
    a= execute ('cat', _in=f)

    a= execute ('cat', _in=['a', 'b'])
