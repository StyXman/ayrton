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

from ayrton.expansion import bash
import ayrton
from ayrton.execute import CommandNotFound

import logging

logger= logging.getLogger ('ayton.tests.ayrton')

# create one of these
ayrton.runner= ayrton.Ayrton ()

class Bash(unittest.TestCase):
    def test_simple_string (self):
        self.assertEqual (bash ('s'), [ 's' ])

    def test_simple_string_single (self):
        self.assertEqual (bash ('s', single=True), 's')

    def test_glob1 (self):
        self.assertEqual (bash ('*.py'), [ 'setup.py' ])

    def test_glob1_single (self):
        self.assertEqual (bash ('*.py', single=True), 'setup.py')

    def test_glob2 (self):
        self.assertEqual (sorted (bash ([ '*.py', '*.txt' ])), [ 'LICENSE.txt', 'requirements.txt', 'setup.py', ])

    def test_glob_brace1 (self):
        self.assertEqual (sorted (bash ('s{a,*.py}')), [ 'sa', 'setup.py' ])

    def test_glob_brace2 (self):
        self.assertEqual (sorted (bash ('ayrton/tests/data/{a,*.py}')), [ 'ayrton/tests/data/a', 'ayrton/tests/data/test.me.py' ])

    def test_simple1_brace (self):
        self.assertEqual (bash ('{acde,b}'), [ 'acde', 'b' ])

    def test_simple2_brace (self):
        self.assertEqual (bash ('a{b,ce}d'), [ 'abd', 'aced' ])

    def test_simple3_brace (self):
        self.assertEqual (bash ('{a}'), [ '{a}' ])

    def test_simple3_brace_single (self):
        self.assertEqual (bash ('{a}', single=True), '{a}')

    def test_simple4_brace (self):
        self.assertEqual (bash ('a}'), [ 'a}' ])

    def test_simple4_brace_single (self):
        self.assertEqual (bash ('a}', single=True), 'a}')

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

    def test_escaped_brace_single (self):
        self.assertEqual (bash ('\{a,b}', single=True), '{a,b}')

    def test_real_example1 (self):
        # tiles/{legend*,Elevation.dgml,preview.png,Makefile}
        pass

    def test_tilde (self):
        self.assertEqual (bash ('~'), [ os.environ['HOME'] ])

    def test_tilde_single (self):
        self.assertEqual (bash ('~', single=True), os.environ['HOME'])

def setUpMockStdout (self):
    # due to the interaction between file descriptors,
    # I better write this down before I forget

    # I save the old stdout in a new fd
    self.old_stdout= os.dup (1)

    # create a pipe; this gives me a read and write fd
    r, w= os.pipe ()

    # I replace the stdout with the write fd
    # this closes 1, but the original stdout is saved in old_stdout
    os.dup2 (w, 1)

    # now I have two fds pointing to the write end of the pipe, stdout and w
    # close w
    os.close (w)

    # create a file() from the reading fd
    # this DOES NOT create a new fd or file
    self.r= open (r, mode='rb')

    # the test will have to close stdin after performing what's testing
    # that's because otherwise the test locks at reading from the read end
    # because there's still that fd available for writing in the pipe
    # there is another copy of that fd, in the child side,
    # but that is closed when the process finished
    # there is still a tricky part to do on tearDownMockStdout()

def tearDownMockStdout (self):
    # restore sanity
    # original stdout into 1, even if we're leaking fd's
    os.dup2 (self.old_stdout, 1)
    os.close (self.old_stdout)
    self.r.close ()
    ayrton.runner.wait_for_pending_children ()

class CommandExecution (unittest.TestCase):
    setUp=    setUpMockStdout
    tearDown= tearDownMockStdout

    def testStdOut (self):
        # do the test
        ayrton.main ('echo ("foo")')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'foo\n')

    def testStdEqNone (self):
        # do the test
        ayrton.main ('echo ("foo", _out=None)')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        # the output is empty, as it went to /dev/null
        self.assertEqual (self.r.read (), b'')

    def testStdEqCapture (self):
        # do the test
        ayrton.main ('''f= echo ("foo", _out=Capture);
print ("echo: %s" % f)''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        # the output is empty, as it went to /dev/null
        # BUG: check why there's a second \n
        # ANS: because echo adds the first one and print adds the second one
        self.assertEqual (self.r.read (), b'echo: foo\n\n')

    def testExitCodeOK (self):
        ayrton.main ('''if true ():
    print ("yes!")''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'yes!\n')

    def testExitCodeNOK (self):
        ayrton.main ('''if not false ():
    print ("yes!")''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'yes!\n')

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

    #def testOptionETrue (self):
        #self.assertRaises (ayrton.CommandFailed,
                           #ayrton.main, '''option (e=True)
#false ()''')

    def testFails (self):
        ayrton.main ('''option ('-e')
false (_fails=True)''')

    def testDotInExecutables (self):
        # add ayrton/tests/data to $PATH
        os.environ['PATH']+= os.pathsep+os.path.join (os.getcwd (), 'ayrton/tests/data')
        logger.debug (os.environ['PATH'])
        ayrton.main ('''test.me.py ()''')

class PipingRedirection (unittest.TestCase):
    setUp=    setUpMockStdout
    tearDown= tearDownMockStdout

    def testPipe (self):
        ayrton.main ('ls () | grep ("setup")')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'setup.py\n')

    def testLongPipe (self):
        ayrton.main ('ls () | grep ("setup") | wc (-l=True)')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'1\n')

    def testGt (self):
        fn= tempfile.mkstemp ()[1]

        ayrton.main ('echo ("yes") > "%s"' % fn)

        contents= open (fn).read ()
        # read() does not return bytes!
        self.assertEqual (contents, 'yes\n')
        os.unlink (fn)

    def testLt (self):
        fd, fn= tempfile.mkstemp ()
        os.write (fd, b'42\n')
        os.close (fd)

        ayrton.main ('cat () < "%s"' % fn)

        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'42\n')
        os.unlink (fn)

    def testLtGt (self):
        fd, fn1= tempfile.mkstemp ()
        os.write (fd, b'43\n')
        os.close (fd)
        fn2= tempfile.mkstemp ()[1]

        ayrton.main ('cat () < "%s" > "%s"' % (fn1, fn2))

        contents= open (fn2).read ()
        # read() does not return bytes!
        self.assertEqual (contents, '43\n')

        os.unlink (fn1)
        os.unlink (fn2)

    def testRShift (self):
        fn= tempfile.mkstemp ()[1]

        ayrton.main ('echo ("yes") > "%s"' % fn)
        ayrton.main ('echo ("yes!") >> "%s"' % fn)

        contents= open (fn).read ()
        # read() does not return bytes!
        self.assertEqual (contents, 'yes\nyes!\n')
        os.unlink (fn)


class MiscTests (unittest.TestCase):
    setUp=    setUpMockStdout
    tearDown= tearDownMockStdout

    def testEnviron (self):
        ayrton.main ('''export (TEST_ENV=44);
run ("./ayrton/tests/data/test_environ.sh")''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'44\n')

    def testUnset (self):
        ayrton.main ('''export (TEST_ENV=45)
print (TEST_ENV)
unset ("TEST_ENV")
try:
    TEST_ENV
except NameError:
    print ("yes")''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'45\nyes\n')

    def testEnvVarAsGlobalVar (self):
        os.environ['testEnvVarAsLocalVar'] = '46' # envvars are strings only
        ayrton.main ('print (testEnvVarAsLocalVar)')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'46\n')

    def testExportSetsGlobalVar (self):
        ayrton.main ('''export (foo=47);
print (foo)''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'47\n')

    def testCwdPwdRename (self):
        ayrton.main ('''import os.path;
print (os.path.split (pwd ())[-1])''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'ayrton\n')

    def testWithCd (self):
        ayrton.main ('''import os.path
with cd ("bin"):
    print (os.path.split (pwd ())[-1])''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'bin\n')

    def testShift (self):
        ayrton.main ('''a= shift ();
print (a)''', argv=['test_script.ay', '48'])
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'48\n')

    def testShifts (self):
        ayrton.main ('''a= shift (2);
print (a)''', argv=['test_script.ay', '49', '27'])
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b"['49', '27']\n")

    def testO (self):
        # this should not explode
        ayrton.main ('''ls (o (full_time=True))''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)

    def testComposing (self):
        # equivalent to testPipe()
        ayrton.main ('grep (ls (), "setup")')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'setup.py\n')

    def testBg (self):
        ayrton.main ('''a= find ("/usr", _bg=True, _out=None);
echo ("yes!");
echo (a.exit_code ())''')
        # close stdout as per the description of setUpMockStdout()
        os.close (1)
        self.assertEqual (self.r.read (), b'yes!\n0\n')
        # ayrton.runner.wait_for_pending_children ()

class CommandDetection (unittest.TestCase):

    def testSimpleCase (self):
        ayrton.main ('true ()')

    def testSimpleCaseFails (self):
        self.assertRaises (CommandNotFound, ayrton.main, 'foo ()')

    def testFromImport (self):
        ayrton.main ('''from random import seed;
seed ()''')

    def testFromImportFails (self):
        self.assertRaises (CommandNotFound, ayrton.main,
                           '''from random import seed;
foo ()''')

    def testFromImportAs (self):
        ayrton.main ('''from random import seed as foo
foo ()''')

    def testFromImportAsFails (self):
        self.assertRaises (CommandNotFound, ayrton.main,
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

    def testDefFun1 (self):
        ayrton.main ('''def foo ():
    true= 40
true ()''')

    def testDefFun2 (self):
        self.assertRaises (ayrton.CommandFailed, ayrton.main, '''option ('errexit')
def foo ():
    false= 41
false ()''')

    def testDefFunFails1 (self):
        ayrton.main ('''option ('errexit')
def foo ():
    false= lambda: True
    false ()''')

    def testCallFun (self):
        ayrton.main ('''def func ():
    true ()

func ()''')

    def testCommanIsPresent (self):
        ayrton.main ('''c= Command ('ls')
c ()''')

    def testInstantiateClass (self):
        ayrton.main ('''class Foo ():
    pass

foo= Foo ()''')

    def testImport (self):
        ayrton.main ('''import math
math.floor (1.1)''')

    def testImportCallFromFunc (self):
        ayrton.main ('''import math
def foo ():
    math.floor (1.1)

foo ()''', 'testImportCallFromFunc')

    def testImportFrom (self):
        ayrton.main ('''from math import floor
floor (1.1)''')

    def testImportFromCallFromFunc (self):
        ayrton.main ('''from math import floor
def foo ():
    floor (1.1)

foo ()''', 'testImportFromCallFromFunc')

    def testUnknown (self):
        try:
            ayrton.main ('''foo''')
        except CommandNotFound:
            raise
        except NameError:
            pass
        self.assertRaises (NameError, ayrton.main, '''fff()''')
        self.assertRaises (CommandNotFound, ayrton.main, '''fff()''')

class ParsingErrors (unittest.TestCase):

    def testTupleAssign (self):
        ayrton.main ('''(a, b)= (1, 2)''')

    def testSimpleFor (self):
        ayrton.main ('''for a in (1, 2): pass''')

class ReturnValues (unittest.TestCase):

    def __testSimpleReturn (self):
        self.assertEqual (ayrton.main ('''return 50'''), 50)

    def testException (self):
        self.assertRaises (SystemError, ayrton.main, '''raise SystemError''')
