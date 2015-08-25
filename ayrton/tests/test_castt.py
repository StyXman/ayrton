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
from ast import Attribute, Name, Load, Subscript, Index, Num

from ayrton import castt
from ayrton.execute import o
import ayrton

class TestBinding (unittest.TestCase):

    def setUp (self):
        self.c= castt.CrazyASTTransformer ({})

    def testSimpleFor (self):
        t= ast.parse ("""for x in (): pass""")

        t= self.c.modify (t)

        self.assertTrue ('x'  in self.c.seen_names)

    def testTupleFor (self):
        t= ast.parse ("""for x, y in (4, 2): pass""")

        t= self.c.modify (t)

        self.assertTrue ('x'  in self.c.seen_names)
        self.assertTrue ('y'  in self.c.seen_names)

    def testImport (self):
        t= ast.parse ("""import os""")

        t= self.c.modify (t)

        self.assertTrue ('os' in self.c.seen_names)

    def testTryExcept (self):
        t= ast.parse ("""try:
    foo()
except Exception as e:
    pass""")

        t= self.c.modify (t)

        self.assertTrue ('e' in self.c.seen_names)

def parse_expression (s):
    # Module(body=[Expr(value=...)])
    return ast.parse (s).body[0].value

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

    def testDoubleKeyword (self):
        c= castt.CrazyASTTransformer ({ 'o': o})
        t= ayrton.parse ("""foo (p= True, p=False)""")

        node= c.visit_Call (t.body[0].value)

        # Call(func=Call(func=Name(id='Command', ctx=Load()), args=[Str(s='foo')], keywords=[], starargs=None, kwargs=None),
        #      args=[Call(func=Name(id='o', ctx=Load()), args=[], keywords=[keyword(arg='p', value=Name(id='True', ctx=Load()))], starargs=None, kwargs=None),
        #            Call(func=Name(id='o', ctx=Load()), args=[], keywords=[keyword(arg='p', value=Name(id='False', ctx=Load()))], starargs=None, kwargs=None)],
        #      keywords=[], starargs=None, kwargs=None)
        # both arguments have the same name!
        self.assertEqual (node.args[0].keywords[0].arg,
                          node.args[1].keywords[0].arg, ast.dump (node))

class TestHelperFunctions (unittest.TestCase):

    def testName (self):
        single, combined= castt.func_name2dotted_exec (parse_expression ('test'))

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test')

    def testDottedName (self):
        single, combined= castt.func_name2dotted_exec (parse_expression ('test.py'))

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test.py')

    def testDottedDottedName (self):
        # NOTE: yes, indentation sucks here
        single, combined= castt.func_name2dotted_exec (parse_expression ('test.me.py'))

        self.assertEqual (single, 'test')
        self.assertEqual (combined, 'test.me.py')

    def testDottedSubscript (self):
        single, combined= castt.func_name2dotted_exec (parse_expression ('argv[3].split'))

        self.assertEqual (single, 'argv')
        # this is a very strange but possible executable name
        self.assertEqual (combined, 'argv[3].split')

    def testDottedSubscriptComplex (self):
        single, combined= castt.func_name2dotted_exec (parse_expression ('argv[3].split[:42]'))

        self.assertEqual (single, 'argv')
        # this is a very strange but possible executable name
        self.assertEqual (combined, 'argv[3].split[:42]')
