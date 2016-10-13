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
import unittest.case
import sys
import io
import os
import tempfile
import os.path
import time
import signal
from socket import socket, AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET
from tempfile import mkstemp
import traceback
import paramiko.ssh_exception

from ayrton.expansion import bash
import ayrton
from ayrton.execute import CommandNotFound
from ayrton.utils import copy_loop, close

import logging

logger= logging.getLogger ('ayton.tests.remote')


class OtherFunctions (unittest.TestCase):

    def test_copy_loop_pipe (self):
        data= 'yabadabadoo'

        pipe= os.pipe ()
        self.addCleanup (close, pipe[0])
        self.addCleanup (close, pipe[1])

        with open (pipe[1], 'w') as w:
            w.write (data)

        r= pipe[0]
        w, dst= mkstemp (suffix='.ayrtmp', dir='.')
        self.addCleanup (os.unlink, dst)

        copy_loop ({ r: w }, buf_len=4)

        with open (dst) as r:
            self.assertEqual (r.read (), data)


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
            logger.debug ('main parent')
            # parent
            self.addCleanup (os.waitpid, pid, 0)

            # give nc time to come up
            time.sleep (0.2)
        else:
            try:
                # child
                logger.debug ('nc')

                server= socket (AF_INET, SOCK_STREAM)
                server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                server.settimeout (3)
                server.bind (('127.0.0.1', 2233))
                server.listen ()

                client, _= server.accept ()
                # bash resets the O_ONONBLOCK flag
                # see below
                # client.settimeout (3)
                close (server)

                logger.debug ('bash')
                os.dup2 (client.fileno (), 0)
                os.dup2 (client.fileno (), 1)
                close (client)

                pid= os.fork ()
                if pid==0:
                    # child             vvvv-- don't forget argv[0]
                    os.execlp ('bash', 'bash')
                    # NOTE: does not return
                    # but if there's a bug, it might
                else:
                    # implement timeout like this
                    time.sleep (2)
                    try:
                        os.kill (pid, signal.SIGKILL)
                    except ChildProcessError:
                        pass
                    os.waitpid (pid, 0)

                # pass through finally
            except Exception as e:
                logger.debug ('*BOOM*')
                traceback.print_exc ()
                logger.debug (traceback.format_exc ())
            finally:
                # connect with the unittest which can be waiting forever
                with socket (AF_INET, SOCK_STREAM) as client:
                    try:
                        client.connect (('127.0.0.1', 4227))
                    except ConnectionRefusedError:
                        pass

                self.commit_suicide ()

    def commit_suicide (self):
        # suicide blonde
        logger.debug ('Goodbye, cruel wrold!')
        os.kill (os.getpid (), signal.SIGKILL)


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


def skip_if_AuthException (test):
    def wrapper (self):
        try:
            test (self)
        except paramiko.ssh_exception.AuthenticationException:
            self.skipTest ("""This test only succeeds if you you have password/passphrase-less access to localhost""")

    return wrapper

class RealRemoteTests (RemoteTests):

    @skip_if_AuthException
    def testLocalVarToRemoteToLocal (self):
        self.runner.run_file ('ayrton/tests/scripts/testLocalVarToRealRemoteToLocal.ay')

        self.assertTrue (self.runner.locals['testLocalVarToRealRemoteToLocal'])


    @skip_if_AuthException
    def testRemoteCommandStdout (self):
        self.runner.run_file ('ayrton/tests/scripts/testRemoteCommandStdout.ay')


    @skip_if_AuthException
    def testRemoteCommandStderr (self):
        self.runner.run_file ('ayrton/tests/scripts/testRemoteCommandStderr.ay')
