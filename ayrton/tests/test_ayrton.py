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

from ayrton.expansion import bash
import ayrton
import sh

class Bash(unittest.TestCase):
    def test_simple_string (self):
        self.assertEqual (bash ('s'), [ 's' ])

    def test_glob1 (self):
        self.assertEqual (sorted (bash ('*.py')), [ 'setup.py' ])

    def test_glob2 (self):
        self.assertEqual (sorted (bash ([ '*.py', '*.txt' ])), [ 'LICENSE.txt', 'setup.py', ])

    def test_glob_brace1 (self):
        self.assertEqual (sorted (bash ('s{a,*.py}')), [ 'sa', 'setup.py' ])

    def test_glob_brace2 (self):
        self.assertEqual (sorted (bash ('ayrton/tests/data/{a,*.py}')), [ 'ayrton/tests/data/a', 'ayrton/tests/data/test.py' ])

    def test_simple1_brace (self):
        self.assertEqual (bash ('{acde,b}'), [ 'acde', 'b' ])

    def test_simple2_brace (self):
        self.assertEqual (bash ('a{b,ce}d'), [ 'abd', 'aced' ])

    def test_simple3_brace (self):
        self.assertEqual (bash ('{a}'), [ '{a}' ])

    def test_simple4_brace (self):
        self.assertEqual (bash ('a}'), [ 'a}' ])

    def test_simple5_brace (self):
        self.assertEqual (bash ('a{bfgh,{ci,djkl}e'), [ 'a{bfgh,cie', 'a{bfgh,djkle' ])

    def test_simple6_brace (self):
        self.assertEqual (bash ('{a,{b,c}d}'), [ 'a', 'bd', 'cd' ])

    def test_simple7_brace (self):
        self.assertEqual (bash ('foo{,bar}'), [ 'foo', 'foobar' ])

    def test_nested1_brace (self):
        # note how this is equivalent to a{b,c,d}e!
        self.assertEqual (bash ('a{b,{c,d}}e'), [ 'abe', 'ace', 'ade' ])

    def test_nested2_brace (self):
        self.assertEqual (bash ('{c{a,b}d,e{f,g}h}'), [ 'cad', 'cbd', 'efh', 'egh' ])

    def test_escaped_brace (self):
        self.assertEqual (bash ('\{a,b}'), [ '{a,b}' ])

    def test_real_example1 (self):
        # tiles/{legend*,Elevation.dgml,preview.png,Makefile}
        pass

    def test_tilde (self):
        self.assertEqual (bash ('~'), [ os.environ['HOME'] ])

class HardExpansion(unittest.TestCase):
    # test cases deemed too hard to comply and corner cases
    # (that is, they can be ignored for a while :)
    pass

class A(object):
    def __init__ (self, buf):
        self.buffer= buf

    # make someone happy
    def flush (self):
        pass

    # make someone else happy
    def write (self, o):
        self.buffer.write (bytes (o, 'utf-8'))

def setUpMockStdout (self):
    self.old_stdout= sys.stdout
    self.a= A (io.BytesIO ())
    sys.stdout= self.a

def tearDownMockStdout (self):
    # restore sanity
    sys.stdout= self.old_stdout

class CommandExecution (unittest.TestCase):
    # for the moment I will just test my changes over sh.Command
    setUp=    setUpMockStdout
    tearDown= tearDownMockStdout

    def testStdOut (self):
        # do the test
        ayrton.main ('echo ("foo")')
        self.assertEqual (self.a.buffer.getvalue (), b'foo\n')

    def testStdEqNone (self):
        # do the test
        ayrton.main ('echo ("foo", _out=None)')
        # the output is empty, as it went to /dev/null
        self.assertEqual (self.a.buffer.getvalue (), b'')

    def testStdEqCapture (self):
        # do the test
        ayrton.main ('''f= echo ("foo", _out=Capture);
print ("echo: %s" % f)''')
        # the output is empty, as it went to /dev/null
        # BUG: check why there's a second \n
        # ANS: because echo adds the first one and print adds the second one
        self.assertEqual (self.a.buffer.getvalue (), b'echo: foo\n\n')

    def testExitCodeOK (self):
        ayrton.main ('''if true ():
    print ("yes!")''')
        self.assertEqual (self.a.buffer.getvalue (), b'yes!\n')

    def testExitCodeNOK (self):
        ayrton.main ('''if not false ():
    print ("yes!")''')
        self.assertEqual (self.a.buffer.getvalue (), b'yes!\n')

    def testOptionErrexit (self):
        self.assertRaises (ayrton.CommandFailed,
                           ayrton.main, '''option ('errexit')
false ()''')

    def testOptionMinus_e (self):
        self.assertRaises (ayrton.CommandFailed,
                           ayrton.main, '''option ('-e')
false ()''')

    def testOptionPlus_e (self):
        ayrton.main ('''option ('+e')
false ()''')

class MiscTests (unittest.TestCase):
    setUp=    setUpMockStdout
    tearDown= tearDownMockStdout

    def testEnviron (self):
        ayrton.main ('''export (TEST_ENV=42);
run ("./ayrton/tests/data/test_environ.sh")''')
        self.assertEqual (self.a.buffer.getvalue (), b'42\n')

    def testUnset (self):
        ayrton.main ('''export (TEST_ENV=42)
print (TEST_ENV)
unset ("TEST_ENV")
try:
    TEST_ENV
except NameError:
    print ("yes")''')
        self.assertEqual (self.a.buffer.getvalue (), b'42\nyes\n')

    def testEnvVarAsGlobalVar (self):
        os.environ['testEnvVarAsLocalVar'] = '42' # envvars are strings only
        ayrton.main ('print (testEnvVarAsLocalVar)')
        self.assertEqual (self.a.buffer.getvalue(), b'42\n')

    def testExportSetsGlobalVar (self):
        ayrton.main ('''export (foo=42);
print (foo)''')
        self.assertEqual (self.a.buffer.getvalue(), b'42\n')

    def testRename (self):
        ayrton.main ('''import os.path;
print (os.path.split (pwd ())[-1])''')
        self.assertEqual (self.a.buffer.getvalue (), b'ayrton\n')

    def testWithCd (self):
        ayrton.main ('''import os.path
with cd ("bin"):
    print (os.path.split (pwd ())[-1])''')
        self.assertEqual (self.a.buffer.getvalue (), b'bin\n')

    def testShift (self):
        ayrton.main ('''a= shift ();
print (a)''', argv=['test_script.ay', '42'])
        self.assertEqual (self.a.buffer.getvalue (), b'42\n')

    def testShifts (self):
        ayrton.main ('''a= shift (2);
print (a)''', argv=['test_script.ay', '42', '27'])
        self.assertEqual (self.a.buffer.getvalue (), b"['42', '27']\n")

    def testSource (self):
        ayrton.main ('''source ("ayrton/tests/source.ay");
print (a)''')
        self.assertEqual (self.a.buffer.getvalue (), b'42\n')

# SSH_CLIENT='127.0.0.1 55524 22'
# SSH_CONNECTION='127.0.0.1 55524 127.0.0.1 22'
# SSH_TTY=/dev/pts/14

    def testRemote (self):
        """This test only succeeds if you you have password/passphrase-less access
        to localhost"""
        ayrton.main ('''a= 42
with remote ('localhost', allow_agent=False) as s:
    print (SSH_CLIENT)
print (s[1].readlines ())''')
        expected1= b'''[b'127.0.0.1 '''
        expected2= b''' 22\\n']\n'''
        self.assertEqual (self.a.buffer.getvalue ()[:len (expected1)], expected1)
        self.assertEqual (self.a.buffer.getvalue ()[-len (expected2):], expected2)

class CommandDetection (unittest.TestCase):

    def testSimpleCase (self):
        ayrton.main ('true ()')

    def testSimpleCaseFails (self):
        self.assertRaises (sh.CommandNotFound, ayrton.main, 'foo ()')

    def testFromImport (self):
        ayrton.main ('''from random import seed;
seed ()''')

    def testFromImportFails (self):
        self.assertRaises (sh.CommandNotFound, ayrton.main,
                           '''from random import seed;
foo ()''')

    def testFromImportAs (self):
        ayrton.main ('''from random import seed as foo
foo ()''')

    def testFromImportAsFails (self):
        self.assertRaises (sh.CommandNotFound, ayrton.main,
                           '''from random import seed as foo
bar ()''')

    def testAssign (self):
        ayrton.main ('''a= lambda x: x
a (1)''')

    def testDel (self):
        self.assertRaises (ayrton.CommandFailed, ayrton.main,
                           '''option ('errexit')
false= lambda: x
del false
false ()''')
