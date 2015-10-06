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
        output= ayrton.main ('''with remote ('127.0.0.1', _debug=True):
    user= USER

return user''', 'testRemoteEnv')

        self.assertEqual (output, os.environ['USER'])


    def testVar (self):
        output= ayrton.main ('''with remote ('127.0.0.1', _debug=True):
    foo= 56

return foo''', 'testRemoteVar')

        self.assertEqual (ayrton.runner.globals['foo'], 56)
        # self.assertEqual (ayrton.runner.locals['foo'], 56)

    def testReturn (self):
        output= ayrton.main ('''with remote ('127.0.0.1', _debug=True) as s:
    return 57


return foo''', 'testRemoteReturn')

        self.assertEqual (output, '''57\n''')


    def testRaisesInternal (self):
        ayrton.main ('''raised= False
try:
    with remote ('127.0.0.1', _debug=True) as s:
        raise SystemError()
except SystemError:
    raised= True


        self.assertEqual (ayrton.runner.globals['raised'], True)

    def testRaisesExternal (self):
        self.assertRaises (SystemError, ayrton.main, '''with remote ('127.0.0.1', _debug=True):
    raise SystemError()''', 'testRaisesExternal')


    def testLocalVarToRemote (self):
        ayrton.main ('''testLocalVarToRemote= True
with remote ('127.0.0.1', _debug=True):
    testLocalVarToRemote''', 'testLocalVarToRemote')


    def __testLocalFunToRemote (self):
        ayrton.main ('''def testLocalFunToRemote(): pass
with remote ('127.0.0.1', _debug=True):
    testLocalFunToRemote''', 'testLocalFunToRemote')


    def __testLocalClassToRemote (self):
        ayrton.main ('''class TestLocalClassToRemote: pass
with remote ('127.0.0.1', _debug=True):
    TestLocalClassToRemote''', 'testLocalClassToRemote')


    def testRemoteVarToLocal (self):
        ayrton.main ('''with remote ('127.0.0.1', _debug=True):
    testRemoteVarToLocal= True
testRemoteVarToLocal''', 'testRemoteVarToLocal')

    def __testLocals (self):
        ayrton.main ('''import ayrton
a= True
l= locals()['a']
# r= ayrton.runner.locals['a']
# ayrton.main() creates a new Ayrton instance and ****s up everything
r= ayrton.runner.run_script ("""return locals()['a']""", 'inception_locals')
assert (l==r)''', 'testLocals')
