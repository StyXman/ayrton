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
