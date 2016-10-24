# (c) 2016 Marcos Dione <mdione@grulic.org.ar>

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

from ayrton.expansion import bash, default
import ayrton

import logging

logger= logging.getLogger ('ayton.tests.expansion')

# create one of these
ayrton.runner= ayrton.Ayrton ()

class TildeExpansion (unittest.TestCase):

    def test_tilde (self):
        self.assertEqual (tilde_expand ('~'), os.environ['HOME'])

    def test_tilde_user (self):
        self.assertEqual (tilde_expand ('~root'), '/root')

    def test_tilde_user_more (self):
        self.assertEqual (tilde_expand ('~root/.'), '/root/.')


class ParameterExpansion (unittest.TestCase):

    def test_default_undefined (self):
        self.assertRaises (NameError, default, 'foo', 'bar')

    def test_default_empty (self):
        ayrton.runner.globals['foo']= ''

        self.assertEqual (default ('foo', 'bar'), 'bar')

        del ayrton.runner.globals['foo']

    def test_default_non_empty (self):
        ayrton.runner.globals['foo']= 'baz'

        self.assertEqual (default ('foo', 'bar'), 'baz')

        del ayrton.runner.globals['foo']

    # def test_default_expanded (self):
    #     self.assertEqual (default ('foo', '~root'), '/root')

    def test_replace_if_set_undef (self):
        self.assertRaises (NameError, replace_if_set, 'foo', 'bar')

    def test_replace_if_set_empty (self):
        ayrton.runner.globals['foo']= ''

        self.assertEqual (replace_if_set ('foo', 'bar'), '')

        del ayrton.runner.globals['foo']


    def do_substr_test (self, offset, length, value):
        ayrton.runner.globals['foo']= self.value

        self.assertEqual (substr ('foo', offset, length), value)

        del ayrton.runner.globals['foo']

    def test_substr_offset (self):
        self.do_substr_test (4, None, self.value[4:])

    def test_substr_offset_length (self):
        self.do_substr_test (4, 2, self.value[4:6])

    def test_substr_offset_too_big (self):
        self.do_substr_test (10, None, '')

    def test_substr_offset_length_too_big (self):
        self.do_substr_test (4, 10, self.value[4:])

    def test_substr_offset_too_big_length (self):
        self.do_substr_test (10, 2, '')


class BraceExpansion(unittest.TestCase):

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

    def test_escaped_brace_inside (self):
        self.assertEqual (bash ('{\{a,b}'), [ '{a', 'b' ])

    def test_escaped_comma (self):
        self.assertEqual (bash ('{a\,b}'), [ '{a,b}' ])

    def test_bam (self):
        self.assertEqual (bash (','), [ ',' ])

    def test_real_example1 (self):
        # tiles/{legend*,Elevation.dgml,preview.png,Makefile}
        pass


# class SequenceExpressionExpansion(unittest.TestCase):
class SequenceExpressionExpansion():

    def test_bam (self):
        self.assertEqual (bash ('{.2}'), [ '{.2}' ])

    def test_not_really (self):
        self.assertEqual (bash ('{1.2}'), [ '{1.2}' ])

    def test_simple (self):
        self.assertEqual (bash ('{1..2}'), [ '1', '2' ])

    def do_not_test_more (self):
        self.assertEqual (bash ('{1..3}'), [ '1', '2', '3' ])

    def do_not_test_escaped_dot_dot (self):
        self.assertEqual (bash ('{1\..2}'), [ '{1..2}' ])

    def do_not_test_dot_escaped_dot (self):
        self.assertEqual (bash ('{1.\.2}'), [ '{1..2}' ])


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

    def test_tilde (self):
        self.assertEqual (bash ('~'), [ os.environ['HOME'] ])

    def test_tilde_single (self):
        self.assertEqual (bash ('~', single=True), os.environ['HOME'])
