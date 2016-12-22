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
import ayrton.execute
import os
import signal
from collections.abc import Iterable

import logging
logger= logging.getLogger ('ayrton.functions')

# NOTE: all this code is executed in the script's environment

class cd (object):
    def __init__ (self, dir):
        self.old_dir= os.getcwd ()
        os.chdir (dir)

    def __enter__ (self):
        pass

    def __exit__ (self, *args):
        os.chdir (self.old_dir)


def define(*varnames, **defaults):
    # defaults have priority over simple names (because they provide a value)
    for varname in varnames:
        if varname not in defaults:
            defaults[varname] = None

    for varname, value in defaults.items():
        if not isinstance(varname, str):
            raise ValueError('variable name cannot be non-string: %r' % varname)

        if varname not in ayrton.runner.globals:
            ayrton.runner.globals[varname] = value


class Exit (Exception):
    # exit() has to be implemented with an exception
    # because sys.exit() makes the whole interpreter go down
    # that is, the interpreter interpreting ayrton :)
    # in fact sys.exit() is *also* implemented with an exception :)
    def __init__ (self, exit_value):
        self.exit_value= exit_value

def exit (value):
    raise Exit (value)


def export (**kwargs):
    for k, v in kwargs.items ():
        ayrton.runner.globals[k]= str (v)
        os.environ[k]= str (v)


option_map= dict (
    e= 'errexit',
    )


def option (option, value=True):
    if len (option)==2:
        if option[0]=='-':
            value= True
        elif option[0]=='+':
            value= False
        else:
            raise ValueError ("Malformed option %r" % option)

        try:
            option= option_map[option[1]]
        except KeyError:
            raise KeyError ("Unrecognized option %r" % option)

    if option not in option_map.values ():
        raise KeyError ("Unrecognized option %r" % option)

    ayrton.runner.options[option]= value


def run (path, *args, **kwargs):
    c= ayrton.execute.Command (path)
    return c (*args, **kwargs)


def shift (*args):
    """`shift()` returns the leftmost element of `argv`.
    `shitf(integer)` return the `integer` leftmost elements of `argv` as a list.
    `shift(iterable)` and `shift(iterable, integer)` operate over `iterable`."""
    if len(args) > 2:
        raise ValueError("shift() takes 0, 1 or 2 arguments.")

    n = 1
    l = ayrton.runner.globals['argv']

    logger.debug2("%s(%d)", args, len(args))
    if len(args) == 1:
        value = args[0]
        logger.debug2(type(value))
        if isinstance(value, int):
            n = value
        elif isinstance(value, Iterable):
            l = value
        else:
            raise ValueError("First parameter must be Iterable or int().")
    elif len(args) == 2:
        l, n = args

    logger.debug2("%s(%d)", args, len(args))
    logger.debug("%s[%d]", l, n)

    if n == 1:
        ans= l.pop(0)
    elif n > 1:
        ans= [ l.pop(0) for i in range(n) ]
    else:
        raise ValueError("Integer parameter must be >= 0.")

    return ans


def trap(handler, *signals):
    for signal in signals:
        signal.signal(signal, handler)


def unset (*args):
    for k in args:
        if k in ayrton.runner.globals:
            # found, remove it
            del ayrton.runner.globals[k]
            del os.environ[k]
