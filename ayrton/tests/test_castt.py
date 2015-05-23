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
from ayrton.execute import o

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

class TestVisits (unittest.TestCase):

    def testFunctionKeywords (self):
        c= castt.CrazyASTTransformer ({ 'dict': dict, 'o': o})
        t= ast.parse ("""dict (a=42)""")

        node= c.visit_Call (t.body[0].value)

        self.assertEqual (len (node.args), 0, ast.dump (node))
        self.assertEqual (len (node.keywords), 1, ast.dump (node))

    def testFunctionOKeywords (self):
        c= castt.CrazyASTTransformer ({ 'dict': dict, 'o': o})
        t= ast.parse ("""dict (o (a=42))""")

        node= c.visit_Call (t.body[0].value)

        self.assertEqual (len (node.args), 0, ast.dump (node))
        self.assertEqual (len (node.keywords), 1, ast.dump (node))

    def testFunctionOArgs (self):
        # NOTE: I need to give the implementation for o();
        # otherwise it will also be converted to Command()
        c= castt.CrazyASTTransformer ({ 'o': o})
        t= ast.parse ("""dict (o (a=42))""")

        node= c.visit_Call (t.body[0].value)

        self.assertEqual (len (node.args), 1, ast.dump (node))
        self.assertEqual (len (node.keywords), 0, ast.dump (node))

class TestHelperFunctions (unittest.TestCase):
    def __init__ (self, *args, **kwargs):
        super ().__init__ (*args, **kwargs)
        self.test= Name(id='test', ctx=Load ())
        self.test_me= Attribute (value=self.test, attr='me', ctx=Load ())
        self.test_me_py= Attribute (value=self.test_me, attr='py', ctx=Load ())

    def testName (self):
        single, combined= castt.func_name2dotted_exec (self.test)

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test')

    def testDottedName (self):
        single, combined= castt.func_name2dotted_exec (self.test_me)

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test.me')

    def testDottedDottedName (self):
        single, combined= castt.func_name2dotted_exec (self.test_me_py)

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test.me.py')
