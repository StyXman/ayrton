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
import os
import random

from ayrton.execute import Command, Capture

echo= Command ('echo', )
cat= Command ('cat', )
ls= Command ('ls')
ssh= Command ('ssh')
mcedit= Command ('mcedit')
bash= Command ('bash')
false= Command ('false')
grep= Command ('grep')

def setUpMockStdOut (self):
    # this is a trick to (hopefulliy) save the original stdout fd
    self.save_stdout= os.dup (1)

    self.pipe= os.pipe ()
    r, w= self.pipe

    # point stdout to w
    os.dup2 (w, 1)
    os.close (w)

    # save the reading fd for reference in the tests
    self.mock_stdout= open (r)

def tearDownMockStdOut (self):
    os.dup2 (self.save_stdout, 1)
    os.close (self.save_stdout)

class MockedStdOut (unittest.TestCase):
    setUp=    setUpMockStdOut

    def testSimple (self):
        echo ('simple')

        # restore stdout before reading,
        # otherwise it gets stuck because there's still one writing side
        tearDownMockStdOut (self)

        self.assertEqual (self.mock_stdout.read (), 'simple\n')
        self.mock_stdout.close ()

    def testInStr (self):
        a= cat (_in='_in=str')
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), '_in=str\n')
        self.mock_stdout.close ()

    def testIbBytes (self):
        a= cat (_in=b'_in=bytes')
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), '_in=bytes\n')
        self.mock_stdout.close ()

    def testInfile (self):
        f= open ('ayrton/tests/data/string_stdin.txt', 'rb')
        a= cat (_in=f)
        f.close ()
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), 'stdin_from_file!\n')
        self.mock_stdout.close ()

    def testInMultiLineSeq (self):
        a= cat (_in=['multi', 'line', 'sequence', 'test'])
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), 'multi\nline\nsequence\ntest\n')
        self.mock_stdout.close ()

    def testInSingleLineSeq (self):
        a= cat (_in=['single,', 'line,', 'sequence,', 'test\n'], _end='')
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), 'single,line,sequence,test\n')
        self.mock_stdout.close ()

    def testInNone (self):
        a= cat (_in=None)
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), '')
        self.mock_stdout.close ()

    def testOutNone (self):
        a= echo ('_out=None', _out=None)
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), '')
        self.mock_stdout.close ()

    def testOutAsIterable (self):
        text= '_out=Capture'
        a= echo (text, _out=Capture)
        tearDownMockStdOut (self)
        for i in a:
            # notice that here there's no \n
            self.assertEqual (i, text)
        self.mock_stdout.close ()

def setUpMockStdErr (self):
    # this is a trick to (hopefulliy) save the original stdout fd
    self.save_stderr= os.dup (1)

    self.pipe= os.pipe ()
    r, w= self.pipe

    # point stdout to w
    os.dup2 (w, 2)
    os.close (w)

    # save the reading fd for reference in the tests
    self.mock_stderr= open (r)

def tearDownMockStdErr (self):
    os.dup2 (self.save_stderr, 2)
    os.close (self.save_stderr)

class MockedStdErr (unittest.TestCase):
    setUp=    setUpMockStdErr

class Redirected (unittest.TestCase):

    def testOutToFile (self):
        file_path= 'ayrton/tests/data/string_stdout.txt'
        r= random.randint (0, 1000000)

        f= open (file_path, 'wb+')
        a= echo ('stdout_to_file: %d' % r, _out=f)
        f.close ()

        f= open (file_path, 'rb')
        self.assertEqual (f.read (), bytes ('stdout_to_file: %d\n' % r, 'ascii'))
        f.close ()
        os.unlink (file_path)

    def testErrToFile (self):
        file_path= 'ayrton/tests/data/string_stderr.txt'
        r= random.randint (0, 1000000)

        f= open (file_path, 'wb+')
        a= ls ('stderr_to_file: %d' % r, _err=f)
        f.close ()

        f= open (file_path, 'rb')
        self.assertEqual (f.read (), bytes ('ls: cannot access stderr_to_file: %d: No such file or directory\n' % r, 'ascii'))
        f.close ()
        os.unlink (file_path)

    def foo (self):
        cat ('ayrton/tests/data/string_stderr.txt')

        a= ls ('_err=None', _err=None)

        a= ls ('_err=Capture', _err=Capture)
        for i in a:
            print (repr (i))

        a= ls ('Makefile', '_err=Capture', _out=Capture, _err=Capture)
        for i in a:
            print (repr (i))

        a= ls (_out=Capture, _chomp=False)
        for i in a:
            print (repr (i))

        # ssh always opens the tty for reading the passphrase, so I'm not sure
        # we can trick it to read it from us
        #a= c.execute ('ssh', 'mx.grulic.org.ar', 'ls -l',
                      #in='passphrase',
                      #_in_tty=True, _out=Capture, _out_tty=True, _err=Capture)
        # a= ssh ('localhost', 'ls -l', _out=Capture)
        # for i in a:
        #     print (repr (i))

        # mcedit ()

        ls (l=True)

        echo (l=True, more=42, kwargs_as_unordered_options='yes!')

        echo (o(l=True), o(more=42), o(o_orders_options='yes!'))

        # NOTE: we convert envvars to str when we export(0 them
        # bash (c='echo $FOO', _env=dict (FOO=42))
        bash (c='echo environments works: $FOO', _env=dict (FOO='yes'))

        if not false ():
            print ('false!')

        # runner.options['errexit']= True

        a= echo ('grep!', _out=Capture)
        grep ('grep', _in=a.readline ())

        f= open ('ayrton/tests/data/string_stdin.txt', 'rb')
        a= cat (_in=f.fileno ())
        f.close ()

        f= open ('ayrton/tests/data/string_stdout.txt', 'wb+')
        a= echo ('stdout_to_file', _out=f.fileno ())
        f.close ()
        cat ('ayrton/tests/data/string_stdout.txt')

        r, w= os.pipe ()
        echo ('pipe!', _out=w)
        os.close (w)
        grep ('pipe', _in=r)
        os.close (r)
