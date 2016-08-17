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


class Exit (Exception):
    # exit() has to be implemented with a exception
    # because sys.exit() makes the whole interpreter go down
    # that is, the interpreter interpreting ayrton :)
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


def shift (n=1):
    # we start at 1 because 0 is the script's path
    # this closely follows bash's behavior
    if n==1:
        ans= ayrton.runner.globals['argv'].pop ()
    elif n>1:
        ans= [ ayrton.runner.globals['argv'].pop ()
               for i in range (n) ]
    else:
        raise ValueError ()

    return ans


def unset (*args):
    for k in args:
        if k in ayrton.runner.globals.keys ():
            # found, remove it
            del ayrton.runner.globals[k]
            del os.environ[k]
