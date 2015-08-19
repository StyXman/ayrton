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
import ast
from ast import Attribute, Name, Load

from ayrton import castt

class TestBinding (unittest.TestCase):

    def testSimpleFor (self):
        c= castt.CrazyASTTransformer ({})
        t= ast.parse ("""for x in (): pass""")
        t= c.modify (t)
        self.assertTrue ('x'  in c.seen_names)

    def testTupleFor (self):
        c= castt.CrazyASTTransformer ({})
        t= ast.parse ("""for x, y in (4, 2): pass""")
        t= c.modify (t)
        self.assertTrue ('x'  in c.seen_names)
        self.assertTrue ('y'  in c.seen_names)

    def testImport (self):
        c= castt.CrazyASTTransformer ({})
        t= ast.parse ("""import os""")
        t= c.modify (t)
        self.assertTrue ('os' in c.seen_names)

def parse (s):
    # Module(body=[Expr(value=...)])
    return ast.parse (s).body[0].value

class TestHelperFunctions (unittest.TestCase):

    def testName (self):
        single, combined= castt.func_name2dotted_exec (parse ('test'))

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test')

    def testDottedName (self):
        single, combined= castt.func_name2dotted_exec (parse ('test.py'))

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test.py')

    def testDottedDottedName (self):
        # NOTE: yes, indentation sucks here
        single, combined= castt.func_name2dotted_exec (parse ('test.me.py'))

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test.me.py')
