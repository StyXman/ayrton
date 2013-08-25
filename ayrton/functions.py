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
import os

def export (**kwargs):
    for k, v in kwargs.items ():
        # NOTE: this is quasi ugly
        ayrton.runner.globals[k]= str (v)
        ayrton.runner.environ[k]= str (v)

def unset (*args):
    for k in args:
        if k in ayrton.runner.environ.keys ():
            # found, remove it
            del ayrton.runner.globals[k]
            del ayrton.runner.environ[k]

def run (path, *args, **kwargs):
    c= ayrton.CommandWrapper._create (path)
    return c (*args, **kwargs)
