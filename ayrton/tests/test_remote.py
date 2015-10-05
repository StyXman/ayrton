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

import unittest
import sys
import io
import os
import tempfile
import os.path
import time

from ayrton.expansion import bash
import ayrton
from ayrton.execute import CommandNotFound

import logging

logger= logging.getLogger ('ayton.tests.remote')


class RemoteTests (unittest.TestCase):

    def setUp (self):
        # create one of these
        # self.runner= ayrton.Ayrton ()
        pass

    def tearDown (self):
        # give time for nc to recover
        time.sleep (0.25)

    def testRemoteEnv (self):
        output= ayrton.main ('''with remote ('127.0.0.1', allow_agent=False, _debug=True) as s:
    user= USER

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s.close ()

return user''', 'testRemoteEnv')

        self.assertEqual (output, os.environ['USER'])

    def testVar (self):
        output= ayrton.main ('''with remote ('127.0.0.1', allow_agent=False, _debug=True) as s:
    foo= 56

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s.close ()

return foo''', 'testRemoteVar')

        self.assertEqual (ayrton.runner.globals['foo'], 56)
        # self.assertEqual (ayrton.runner.locals['foo'], 56)

    def testReturn (self):
        output= ayrton.main ('''with remote ('127.0.0.1', allow_agent=False, _debug=True) as s:
    return 57

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s.close ()

return foo''', 'testRemoteReturn')

        self.assertEqual (output, '''57\n''')

    def testRaisesInternal (self):
        ayrton.main ('''raised= False
try:
    with remote ('127.0.0.1', allow_agent=False, _debug=True) as s:
        raise Exception()
except Exception:
    raised= True

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s.close ()''', 'testRaisesInternal')

        self.assertEqual (ayrton.runner.globals['raised'], True)

    def testRaisesExternal (self):
        self.assertRaises (Exception, ayrton.main, '''with remote ('127.0.0.1', allow_agent=False, _debug=True):
    raise Exception()''', 'testRaisesExternal')
