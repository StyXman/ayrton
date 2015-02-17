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

from ayrton.execute import Command, Capture, o
import ayrton

# create one of these
ayrton.runner= ayrton.Ayrton ()

echo= Command ('echo', )
cat= Command ('cat', )
ls= Command ('ls')
ssh= Command ('ssh')
mcedit= Command ('mcedit')
bash= Command ('bash')
true= Command ('true')
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

    def testInBytes (self):
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

    def testKwargsAsUnorderedOptions (self):
        echo (l=True, more=42, kwargs_as_unordered_options='yes!')
        tearDownMockStdOut (self)

        output= self.mock_stdout.read ()
        # we can't know for sure the order of the options in the final command line
        # '-l --more 42 --kwargs_as_unordered_options yes!\n'
        self.assertTrue ('-l' in output)
        self.assertTrue ('--more 42' in output)
        self.assertTrue ('--kwargs_as_unordered_options yes!' in output)
        self.assertTrue (output[-1]=='\n')
        self.mock_stdout.close ()

    def testOOrdersOptions (self):
        echo (o(l=True), o(more=42), o(o_orders_options='yes!'))
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), '-l --more 42 --o_orders_options yes!\n')
        self.mock_stdout.close ()

    def testEnvironment (self):
        # NOTE: we convert envvars to str when we export() them
        bash (c='echo environments works: $FOO', _env=dict (FOO='yes'))
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), 'environments works: yes\n')
        self.mock_stdout.close ()

    def testIterable (self):
        self.maxDiff= None
        ayrton.main ('''lines_read= 0

for line in echo ('yes'):
    if line=='yes':
        print ('yes!')
    else:
        print (repr (line))

    lines_read+= 1

print (lines_read)''')
        tearDownMockStdOut (self)
        self.assertEqual (self.mock_stdout.read (), 'yes!\n1\n')

def setUpMockStdErr (self):
    # save the original stderr fd
    self.save_stderr= os.dup (1)

    self.pipe= os.pipe ()
    r, w= self.pipe

    # point stderr to w
    os.dup2 (w, 2)
    os.close (w)

    # save the reading fd for reference in the tests
    self.mock_stderr= open (r)

def tearDownMockStdErr (self):
    os.dup2 (self.save_stderr, 2)
    os.close (self.save_stderr)

class MockedStdErr (unittest.TestCase):
    setUp=    setUpMockStdErr

    def testErrNone (self):
        a= ls ('_err=None', _err=None)
        tearDownMockStdErr (self)
        self.assertEqual (self.mock_stderr.read (), '')
        self.mock_stderr.close ()

class Redirected (unittest.TestCase):

    def testInAsFd (self):
        f= open ('ayrton/tests/data/string_stdin.txt', 'rb')
        a= cat (_in=f.fileno (), _out=Capture)
        f.close ()

        l= a.readline ()
        self.assertEqual (l, 'stdin_from_file!')
        a.close ()

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

    def testOutAsIterable (self):
        text= '_out=Capture'
        a= echo (text, _out=Capture)
        for i in a:
            # notice that here there's no \n
            self.assertEqual (i, text)

    def testOutAsFd (self):
        file_path= 'ayrton/tests/data/string_stdout.txt'
        r= random.randint (0, 1000000)

        f= open (file_path, 'wb+')
        a= echo ('stdout_to_fd: %d' % r, _out=f.fileno ())
        f.close ()

        f= open (file_path, 'rb')
        self.assertEqual (f.read (), bytes ('stdout_to_fd: %d\n' % r, 'ascii'))
        f.close ()
        os.unlink (file_path)

    def testErrToFile (self):
        file_path= 'ayrton/tests/data/string_stderr.txt'
        r= random.randint (0, 1000000)

        f= open (file_path, 'wb+')
        a= ls ('stderr_to_file: %d' % r, _err=f)
        f.close ()

        f= open (file_path, 'rb')
        self.assertEqual (f.read (), bytes ('/bin/ls: cannot access stderr_to_file: %d: No such file or directory\n' % r, 'ascii'))
        f.close ()
        os.unlink (file_path)

    def testErrCapture (self):
        a= ls ('_err=Capture', _err=Capture)
        for i in a:
            self.assertEqual (i, '/bin/ls: cannot access _err=Capture: No such file or directory')

    def testOutErrCaptured (self):
        a= ls ('Makefile', '_err=Capture', _out=Capture, _err=Capture)
        # list() exercises __iter__()
        l= list (a)
        self.assertEqual (l[0], '/bin/ls: cannot access _err=Capture: No such file or directory')
        self.assertEqual (l[1], 'Makefile')

    def testPipe (self):
        r, w= os.pipe ()
        echo ('pipe!', _out=w)
        os.close (w)
        a= grep ('pipe', _in=r, _out=Capture)
        os.close (r)

        l= a.readline ()
        self.assertEqual (l, 'pipe!')
        a.close ()

class CommandExecution (unittest.TestCase):
    def testFalse (self):
        a= false ()
        self.assertEqual (a.exit_code (), 1)

    def testTrue (self):
        a= true ()
        self.assertEqual (a.exit_code (), 0)

    def testIfTrue (self):
        if not true ():
            self.fail ()

    def testIfFrue (self):
        if false ():
            self.fail ()

    def testCatGrep (self):
        a= cat (_in=['grap not found', 'grep found', 'grip not found, fell'],
                 _out=Capture)
        b= grep ('grep', _in=a.readlines (), _out=Capture)
        self.assertEqual (b.readline (), 'grep found')
        for i in b:
            raise ValueError ("too many lines")

    def testCatGrep2 (self):
        a= cat (_in=['grap not found', 'grep found', 'grip not found, fell'],
                 _out=Capture)
        b= grep ('grep', _in=a, _out=Capture)
        self.assertEqual (b.readline (), 'grep found')
        for i in b:
            raise ValueError ("too many lines")

    def foo (self):
        # ssh always opens the tty for reading the passphrase, so I'm not sure
        # we can trick it to read it from us
        #a= c.execute ('ssh', 'mx.grulic.org.ar', 'ls -l',
                      #in='passphrase',
                      #_in_tty=True, _out=Capture, _out_tty=True, _err=Capture)
        # a= ssh ('localhost', 'ls -l', _out=Capture)
        # for i in a:
        #     print (repr (i))

        # mcedit ()

        # runner.options['errexit']= True
        pass
