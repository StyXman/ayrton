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

from ayrton.expansion import bash
import ayrton

class Bash(unittest.TestCase):
    def test_simple_string (self):
        self.assertEqual (bash ('s'), ['s'])

    def test_glob1 (self):
        self.assertEqual (sorted (bash ('*.py')), [ 'setup.py' ])

    def test_glob2 (self):
        self.assertEqual (sorted (bash (['*.py', '*.txt'])), [ 'LICENSE.txt', 'TODO.txt', 'setup.py', ])

    def test_glob_brace1 (self):
        self.assertEqual (sorted (bash ('{a,*.py}')), [ 'a', 'setup.py' ])

    def test_glob_brace2 (self):
        self.assertEqual (sorted (bash ('ayrton/tests/data/{a,*.py}')), [ 'ayrton/tests/data/a', 'ayrton/tests/data/test.py' ])

    def test_simple1_brace (self):
        self.assertEqual (bash ('{a,b}'), ['a', 'b'])

    def test_simple2_brace (self):
        self.assertEqual (bash ('a{b,c}d'), ['abd', 'acd'])

    def test_simple3_brace (self):
        self.assertEqual (bash ('{a}'), ['{a}'])

    def test_simple4_brace (self):
        self.assertEqual (bash ('a}'), ['a}'])

    def test_simple5_brace (self):
        self.assertEqual (bash ('a{b,{c,d}e'), ['a{b,ce', 'a{b,de'])

    def test_simple6_brace (self):
        self.assertEqual (bash ('{a,{b,c}d}'), ['a', 'bd', 'cd'])

    def test_simple7_brace (self):
        self.assertEqual (bash ('foo{,bar}'), ['foo', 'foobar' ])

    def test_nested1_brace (self):
        # note how this is equivalent to a{b,c,d}e!
        self.assertEqual (bash ('a{b,{c,d}}e'), ['abe', 'ace', 'ade'])

    def test_nested2_brace (self):
        self.assertEqual (bash ('{c{a,b}d,e{f,g}h}'), ['cad', 'cbd', 'efh', 'egh'])

    def test_escaped_brace (self):
        self.assertEqual (bash ('\{a,b}'), ['{a,b}'])

    def test_real_example1 (self):
        # tiles/{legend*,Elevation.dgml,preview.png,Makefile}
        pass

class HardExpansion(unittest.TestCase):
    # test cases deemed hard to comply and corner cases
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

class CommandExecution (unittest.TestCase):
    # for the moment I will just test my changes over sh.Command

    def testStdOut (self):
        old_stdout= sys.stdout
        a= A (io.BytesIO ())
        sys.stdout= a

        # do the test
        ayrton.main ('echo ("foo")')
        self.assertEqual (a.buffer.getvalue (), b'foo\n')

        # restore sanity
        sys.stdout= old_stdout

    def testStdEqNone (self):
        old_stdout= sys.stdout
        a= A (io.BytesIO ())
        sys.stdout= a

        # do the test
        ayrton.main ('echo ("foo", _out=None)')
        # the output is empty, as it went to /dev/null
        self.assertEqual (a.buffer.getvalue (), b'')

        # restore sanity
        sys.stdout= old_stdout

    def testStdEqCapture (self):
        old_stdout= sys.stdout
        a= A (io.BytesIO ())
        sys.stdout= a

        # do the test
        ayrton.main ('f= echo ("foo", _out=Capture); print ("echo: %s" % f)')
        # the output is empty, as it went to /dev/null
        # BUG: check why tehre's asecond \n
        self.assertEqual (a.buffer.getvalue (), b'echo: foo\n\n')

        # restore sanity
        sys.stdout= old_stdout

class ExportTest (unittest.TestCase):

    def testEnviron (self):
        old_stdout= sys.stdout
        a= A (io.BytesIO ())
        sys.stdout= a

        ayrton.main ('export (TEST_ENV=42); run ("./ayrton/tests/data/test_environ.sh")')
        self.assertEqual (a.buffer.getvalue (), b'42\n')

        # restore sanity
        sys.stdout= old_stdout