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
from ayrton.parser.pyparser.pyparse import PythonParser, CompileInfo
from ayrton.parser.astcompiler.astbuilder import ast_from_node
import ast
from functools import reduce
import operator

class Parser(unittest.TestCase):
    def setUp (self):
        self.parser= PythonParser (None)
        self.info= CompileInfo('test_parser.py', 'exec')

    def equal (self, a, b):
        # ast.AST does not has a good definitoion of __eq__
        # so I have to make my own
        eq= True
        # print (a, b)

        try:
            items= a.__dict__.items ()
        except AttributeError:
            # no __dict__ means simple value
            # just compare them directly
            # print (a, b, a==b)
            eq= a==b
        else:
            for k, v1 in items:
                try:
                    v2= b.__dict__[k]
                except KeyError:
                    # print ('here3')
                    eq= False
                    break
                else:
                    # print (k, v1, v2)
                    # skip special stuff
                    if k.startswith ('__'):
                        continue
                    # methods too
                    if callable (v1):
                        continue

                        if type (v1) in (list, tuple):
                            for e1, e2 in zip (v1, v2):
                                if not self.equal (e1, e2):
                                    # print ('here1')
                                    eq= False
                                    break
                        else:
                            eq= eq and self.equal (v1, v2)
                        if not eq:
                            # print ('here2')
                            break

        # print (eq)
        return eq

    def parse (self, source):
        t= self.parser.parse_source (source, self.info)
        ast1= ast_from_node (None, t, self.info)
        ast2= ast.parse (source)
        self.assertTrue (self.equal (ast1, ast2),
                         "\n%s != \n%s" % (ast.dump (ast1), ast.dump (ast2)))

    def test_comp (self):
        self.parse ('[ x for x in foo() ]')

    def test_comp_if (self):
        self.parse ('[ x for x in foo() if x ]')
