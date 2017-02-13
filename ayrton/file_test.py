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
import stat
import os.path

import logging
logger= logging.getLogger ('ayrton.file_test')

# these functions imitate the -* tests from [ (as per bash's man page)

def simple_stat (fname):
    try:
        return os.stat (fname)
    except (IOError, OSError):
        return None


class FalseBool:
    """This class is needed so file test X() can be called -X() and not break
    the semantics. The problem is that -True==-1 and -False==0. Also:
    TypeError: type 'bool' is not an acceptable base type."""

    def __init__ (self, value):
        if not isinstance (value, bool):
            raise ValueError

        self.value= value

    def __bool__ (self):
        return self.value

    def __neg__ (self):
        return self.value


def a (fname):
    return FalseBool (simple_stat (fname) is not None)

def b (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and stat.S_ISBLK (s.st_mode))

def c (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and stat.S_ISCHR (s.st_mode))

def d (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and stat.S_ISDIR (s.st_mode))

# both return the same thing!
e= a

def f (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and stat.S_ISREG (s.st_mode))

def g (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and (stat.S_IMODE (s.st_mode) & stat.S_ISGID)!=0)

def h (fname):
    return FalseBool (os.path.islink (fname))

def k (fname):
    s= simple_stat (fname)
    # VTX?!?
    return FalseBool (s is not None and (stat.S_IMODE (s.st_mode) & stat.S_ISVTX)!=0)

def p (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and stat.S_ISFIFO (s.st_mode))

def r (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and (stat.S_IMODE (s.st_mode) &
                                         (stat.S_IRUSR|stat.S_IRGRP|stat.S_IROTH))!=0)

def s (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and s.st_size>0)

# TODO: t
# os.isatty(fd)

def u (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and (stat.S_IMODE (s.st_mode) & stat.S_ISUID)!=0)

def w (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and (stat.S_IMODE (s.st_mode) &
                                         (stat.S_IWUSR|stat.S_IWGRP|stat.S_IWOTH))!=0)

def x (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and (stat.S_IMODE (s.st_mode) &
                                         (stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH))!=0)

# TODO: G, O

L= h

def N (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and s.st_mtime_ns > s.st_atime_ns)

def S (fname):
    s= simple_stat (fname)
    return FalseBool (s is not None and stat.S_ISSOCK (s.st_mode))

# TODO: ef,

def nt (a, b):
    # file1 is newer (according to modification date) than file2, or if file1 exists and file2 does not.
    s1= simple_stat (a)
    s2= simple_stat (b)
    return FalseBool (   (s1 is not None and s2 is None)
                      or (s1.st_mtime_ns > s2.st_mtime_ns))

def ot (a, b):
    # file1 is older than file2, or if file2 exists and file1 does not.
    s1= simple_stat (a)
    s2= simple_stat (b)
    return FalseBool (   (s2 is not None and s1 is None)
                      or (s2.st_mtime_ns > s1.st_mtime_ns))

# string
def z(value):
    ans = value is None or value == ''

    return FalseBool(ans)
