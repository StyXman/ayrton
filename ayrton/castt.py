# -*- coding: utf-8 -*-

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

import ast
from ast import Pass, Module, Bytes, copy_location, Call, Name, Load, Str
from ast import fix_missing_locations, Import, alias, Attribute, ImportFrom
import pickle

class CrazyASTTransformer (ast.NodeTransformer):
    def __init__ (self, environ):
        super ().__init__ ()
        self.environ= environ
        self.known_names= set ()

    # The following constructs bind names:
    # [ ] formal parameters to functions,
    # [x] import statements,
    # [ ] class and function definitions (these bind the class or function name
    #     in the defining block),
    # [x] and targets that are identifiers if occurring in an assignment,
    # [ ] for loop header, or
    # [ ] after as in a with statement
    # [ ] or except clause.
    # The import statement of the form from ... import * binds all names defined
    # in the imported module, except those beginning with an underscore.

    # A block is a piece of Python program text that is executed as a unit.
    # The following are blocks:
    # [ ] a module,
    # [ ] a function body, and
    # [ ] a class definition.
    # [ ] A script file is a code block.
    # [ ] The string argument passed to the built-in functions eval() and exec()
    #     is a code block.

    # A scope defines the visibility of a name within a block. If a local variable
    # is defined in a block, its scope includes that block. If the definition
    # occurs in a function block, the scope extends to any blocks contained within
    # the defining one, unless a contained block introduces a different binding
    # for the name. The scope of names defined in a class block is limited to the
    # class block; it does not extend to the code blocks of methods – this
    # includes comprehensions and generator expressions since they are implemented
    # using a function scope.

    # [ ] A target occurring in a del statement is also considered bound for this
    #     purpose (though the actual semantics are to unbind the name).

    def visit_Import (self, node):
        self.generic_visit (node)
        # Import(names=[alias(name='foo', asname=None)])
        for name in node.names:
            if name.asname is not None:
                self.known_names.add (name.asname)
            else:
                self.known_names.add (name.name)
        return node

    visit_ImportFrom= visit_Import
        # ImportFrom(module='bar', names=[alias(name='baz', asname=None)], level=0)

    def visit_Call (self, node):
        self.generic_visit (node)
        # Call(func=Name(id='b', ctx=Load()), args=[], keywords=[], starargs=None,
        #      kwargs=None)
        if   type (node.func)==ast.Name:
            func_name= node.func.id
            if func_name not in self.known_names:
                try:
                    # fisrt check if it's not one of the builtin functions
                    self.environ[func_name]
                except KeyError:
                    # I guess I have no other option bu to try to execute somehting here...
                    new_node= Call (func=Attribute (value=Name (id='CommandWrapper', ctx=Load ()),
                                                    attr='_create', ctx=Load ()),
                                    args=[Str (s=func_name)], keywords=[],
                                    starargs=None, kwargs=None)
                    ast.copy_location (new_node, node)
                    ast.fix_missing_locations (new_node)
                    node.func= new_node

        return node

    def visit_Assign (self, node):
        self.generic_visit (node)
        # Assign(targets=[Name(id='a', ctx=Store())], value=Num(n=2))
        for target in node.targets:
            self.known_names.add (target.id)

        return node

    def visit_Delete (self, node):
        self.generic_visit (node)
        # Delete(targets=[Name(id='foo', ctx=Del())])
        for target in node.targets:
            self.known_names.remove (target.id)

        return node

    def visit_With (self, node):
        self.generic_visit (node)
        # With(context_expr=Call(func=Name(id='foo', ctx=Load()), args=[],
        #                        keywords=[], starargs=None, kwargs=None),
        #      optional_vars=Name(id='bar', ctx=Store()), ...)
        call= node.items[0].context_expr
        # TODO: more checks
        if call.func.id=='remote':
            # capture the body and put it as the first argument to ssh()
            # but within a module, and already pickled;
            # otherwise we need to create an AST for the call of all the
            # constructors in the body we capture... it's complicated
            m= Module (body=node.body)

            data= pickle.dumps (m)
            s= Bytes (s=data)
            s.lineno= node.lineno
            s.col_offset= node.col_offset
            call.args.insert (0, s)

            p= Pass ()
            p.lineno= node.lineno+1
            p.col_offset= node.col_offset+4

            node.body= [ p ]

        return node
