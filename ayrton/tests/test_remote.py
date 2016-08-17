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

import unittest
import sys
import io
import os
import tempfile
import os.path
import time
import signal

from ayrton.expansion import bash
import ayrton
from ayrton.execute import CommandNotFound

import logging

logger= logging.getLogger ('ayton.tests.remote')


class RemoteTests (unittest.TestCase):

    def setUp (self):
        # create one of these
        self.runner= ayrton.Ayrton ()


class DebugRemoteTests (RemoteTests):

    def setUp (self):
        super ().setUp ()

        # fork and execute nc
        pid= os.fork ()
        if pid!=0:
            # parent
            self.child= pid
            # give nc time to come up
            time.sleep (0.2)
        else:
            # child          vvvv-- don't forget argv[0]
            os.execlp ('nc', 'nc', '-l', '-s', '127.0.0.1', '-p', '2233', '-e', '/bin/bash')
            # NOTE: does not return

    def tearDown (self):
        os.kill (self.child, signal.SIGKILL)

    def testRemoteEnv (self):
        self.runner.run_script ('''with remote ('127.0.0.1', _debug=True):
    user= USER''', 'testRemoteEnv.py')

        self.assertEqual (self.runner.locals['user'], os.environ['USER'])


    def testRemoteVar (self):
        self.runner.run_script ('''with remote ('127.0.0.1', _debug=True):
    testRemoteVar= 56''', 'testRemoteVar.py')

        self.assertEqual (self.runner.locals['testRemoteVar'], 56)


    def testRaisesInternal (self):
        self.runner.run_script ('''raised= False

try:
    with remote ('127.0.0.1', _debug=True):
        raise SystemError()
except SystemError:
    raised= True''', 'testRaisesInternal.py')

        self.assertTrue (self.runner.locals['raised'])


    def testRaisesExternal (self):
        self.assertRaises (SystemError, self.runner.run_script,
                           '''with remote ('127.0.0.1', _debug=True):
    raise SystemError()''', 'testRaisesExternal.py')


    def testLocalVarToRemote (self):
        self.runner.run_script ('''testLocalVarToRemote= True

with remote ('127.0.0.1', _debug=True):
    assert (testLocalVarToRemote)''', 'testLocalVarToRemote.py')


    def __testLocalFunToRemote (self):
        self.runner.run_script ('''def testLocalFunToRemote(): pass

with remote ('127.0.0.1', _debug=True):
    testLocalFunToRemote''', 'testLocalFunToRemote.py')


    def __testLocalClassToRemote (self):
        self.runner.run_script ('''class TestLocalClassToRemote: pass

with remote ('127.0.0.1', _debug=True):
    TestLocalClassToRemote''', 'testLocalClassToRemote.py')


    def testRemoteVarToLocal (self):
        self.runner.run_script ('''with remote ('127.0.0.1', _debug=True):
    testRemoteVarToLocal= True''', 'testRemoteVarToLocal.py')

        self.assertTrue (self.runner.locals['testRemoteVarToLocal'])


    def testLocalVarToRemoteToLocal (self):
        self.runner.run_script ('''testLocalVarToRemoteToLocal= False

with remote ('127.0.0.1', _debug=True):
    testLocalVarToRemoteToLocal= True''', 'testLocalVarToRemoteToLocal.py')

        self.assertTrue (self.runner.locals['testLocalVarToRemoteToLocal'])


    def testRemoteCommandStdout (self):
        self.runner.run_script ('''with remote ('127.0.0.1', _debug=True):
    ls(-l=True)''', 'testRemoteCommand.py')


    def testRemoteCommandStderr (self):
        self.runner.run_script ('''with remote ('127.0.0.1', _debug=True):
    ls('foobarbaz')''', 'testRemoteCommand.py')


class RealRemoteTests (RemoteTests):

    def testLocalVarToRemoteToLocal (self):
        """This test only succeeds if you you have password/passphrase-less access to localhost"""
        self.runner.run_file ('ayrton/tests/scripts/testLocalVarToRealRemoteToLocal.ay')

        self.assertTrue (self.runner.locals['testLocalVarToRealRemoteToLocal'])


    def testRemoteCommandStdout (self):
        """This test only succeeds if you you have password/passphrase-less access to localhost"""
        self.runner.run_file ('ayrton/tests/scripts/testRemoteCommandStdout.ay')



    def testRemoteCommandStderr (self):
        """This test only succeeds if you you have password/passphrase-less access to localhost"""
        self.runner.run_file ('ayrton/tests/scripts/testRemoteCommandStderr.ay')
