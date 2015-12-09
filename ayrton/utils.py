# -*- coding: utf-8 -*-

# (c) 2015 Marcos Dione <mdione@grulic.org.ar>

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

import logging
import functools

# TODO: there's probably a better way to do this
def debug2 (self, msg, *args, **kwargs):
    if self.manager.disable>=logging.DEBUG2:
        return

    if logging.DEBUG2>=self.getEffectiveLevel ():
        self._log (logging.DEBUG2, msg, args, **kwargs)


def debug3 (self, msg, *args, **kwargs):
    if self.manager.disable>=logging.DEBUG3:
        return

    if logging.DEBUG3>=self.getEffectiveLevel ():
        self._log (logging.DEBUG3, msg, args, **kwargs)


def patch_logging ():
    # based on https://mail.python.org/pipermail/tutor/2007-August/056243.html
    logging.DEBUG2= 9
    logging.DEBUG3= 8

    logging.addLevelName (logging.DEBUG2, 'DEBUG2')
    logging.addLevelName (logging.DEBUG3, 'DEBUG3')

    logging.Logger.debug2= debug2
    logging.Logger.debug3= debug3


patch_logging ()


def any_comparator (a, b):
    try:
        if a==b:
            return 0
        elif a<b:
            return -1
        else:
            return 1
    except TypeError:
        return any_comparator (str (type (a)), str (type (b)))


def dump_dict (d, level=1):
    if d is not None:
        strings= []

        if level==0:
            strings.append ("{\n")
        for k in sorted (d.keys (), key=functools.cmp_to_key (any_comparator)):
            v= d[k]
            if type (v)!=dict:
                strings.append ("%s%r: %r,\n" % ( '    '*level, k, v ))
            else:
                strings.append ("%s%r: {\n"   % ( '    '*level, k))
                strings.extend (dump_dict (v, level+1))
                strings.append ("%s},\n"      % ( '    '*level, ))
        if level==0:
            strings.cappend ("}\n")

        return ''.join (strings)
    else:
        return 'None'
