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

# create one of these
ayrton.runner= ayrton.Ayrton ()

class RemoteTests (unittest.TestCase):
    def testRemote (self):
        """This test only succeeds if you you have password/passphrase-less access
        to localhost"""
        output= ayrton.main ('''with remote ('127.0.0.1', allow_agent=False) as s:
    print (USER)

value= s[1].readlines ()

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s[0].close ()
s[1].close ()
#s[2].close ()

return value''')

        self.assertEqual ( output, [ ('%s\n' % os.environ['USER']) ] )
        # give time for nc to recover
        time.sleep (0.25)

# SSH_CLIENT='127.0.0.1 55524 22'
# SSH_CONNECTION='127.0.0.1 55524 127.0.0.1 22'
# SSH_TTY=/dev/pts/14
    def testRemoteEnv (self):
        """This test only succeeds if you you have password/passphrase-less access
        to localhost"""
        output= ayrton.main ('''with remote ('127.0.0.1', allow_agent=False) as s:
    print (SSH_CLIENT)

value= s[1].readlines ()

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s[0].close ()
s[1].close ()
s[2].close ()

return value''')

        expected1= '''127.0.0.1 '''
        expected2= ''' 22\n'''
        self.assertEqual (output[0][:len (expected1)], expected1)
        self.assertEqual (output[0][-len (expected2):], expected2)
        # give time for nc to recover
        time.sleep (0.25)

    def testRemoteVar (self):
        """This test only succeeds if you you have password/passphrase-less access
        to localhost"""
        output= ayrton.main ('''with remote ('127.0.0.1', allow_agent=False, _debug=True) as s:
    foo= 56

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s[0].close ()
s[1].close ()
s[2].close ()

try:
    return foo
except Exception as e:
    return e''')

        self.assertEqual (output, '''56\n''')
        # give time for nc to recover
        time.sleep (0.25)

    def testRemoteReturn (self):
        """This test only succeeds if you you have password/passphrase-less access
        to localhost"""
        output= ayrton.main ('''with remote ('127.0.0.1', allow_agent=False, _debug=True) as s:
    return 57

# close the fd's, otherwise the test does not finish because the paramiko.Client() is waiting
# this means even more that the current remote() API sucks
s[0].close ()
s[1].close ()
#s[2].close ()

try:
    return foo
except Exception as e:
    return e''')

        self.assertEqual (output, '''57\n''')
        # give time for nc to recover
        time.sleep (0.25)

