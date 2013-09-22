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
from collections import defaultdict

def append_to_tuple (t, o):
    l= list (t)
    l.append (o)
    return tuple (l)

def pop_from_tuple (t, n=-1):
    l= list (t)
    l.pop (n)
    return tuple (l)

class CrazyASTTransformer (ast.NodeTransformer):
    def __init__ (self, environ):
        super ().__init__ ()
        self.environ= environ
        self.known_names= defaultdict (lambda: 0)
        self.stack= ()
        self.defined_names= defaultdict (lambda: [])

    # The following constructs bind names:
    # [x] formal parameters to functions,
    # [x] import statements,
    # [x] class and
    # [x] function definitions (these bind the class or function name
    #     in the defining block),
    # [x] and targets that are identifiers if occurring in an assignment,
    # [x] for loop header, or
    # [x] after as in a with statement
    # [ ] or except clause.
    # The import statement of the form from ... import * binds all names defined
    # in the imported module, except those beginning with an underscore.

    # A block is a piece of Python program text that is executed as a unit.
    # The following are blocks:
    # [ ] a module,
    # [x] a function body, and
    # [x] a class definition.
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

    # [x] A target occurring in a del statement is also considered bound for this
    #     purpose (though the actual semantics are to unbind the name).

    def visit_Import (self, node):
        self.generic_visit (node)
        # Import(names=[alias(name='foo', asname=None)])
        for name in node.names:
            if name.asname is not None:
                n= name.asname
            else:
                n= name.name
            self.known_names[n]+=1
            self.defined_names[self.stack].append (n)

        return node

    visit_ImportFrom= visit_Import
        # ImportFrom(module='bar', names=[alias(name='baz', asname=None)], level=0)

    def visit_ClassDef (self, node):
        # ClassDef(name='foo', bases=[], keywords=[], starargs=None, kwargs=None,
        #          body=[Pass()], decorator_list=[])
        self.stack= append_to_tuple (self.stack, node.name)
        self.generic_visit (node)

        # take out the function from the stack
        names= self.defined_names[self.stack]
        self.stack= pop_from_tuple (self.stack)
        # ... and remove the names defined in it from the known_names
        for name in names:
            self.known_names[name]-= 1

        return node

    def visit_FunctionDef (self, node):
        # FunctionDef(name='foo',
        #             args=arguments(args=[arg(arg='a', annotation=None),
        #                                  arg(arg='b', annotation=None)],
        #                            vararg='args', varargannotation=None,
        #                            kwonlyargs=[], kwarg='kwargs',
        #                            kwargannotation=None, defaults=[Num(n=1)],
        #                            kw_defaults=[]),
        #             body=[Pass()], decorator_list=[], returns=None)
        self.stack= append_to_tuple (self.stack, node.name)

        # add the arguments as local names
        for arg in node.args.args:
            self.known_names[arg.arg]+= 1
            self.defined_names[self.stack].append (arg.arg)

        self.generic_visit (node)

        # take out the function from the stack
        names= self.defined_names[self.stack]
        self.stack= pop_from_tuple (self.stack)
        # ... and remove the names defined in it from the known_names
        for name in names:
            self.known_names[name]-= 1

        return node

    def visit_For (self, node):
        # For(target=Name(id='x', ctx=Store()), iter=List(elts=[], ctx=Load()),
        #     body=[Pass()], orelse=[])
        for name in node.target:
            self.known_names[name.id]+= 1
            self.defined_names[self.stack].append (name.id)

        self.generic_visit (node)

        return node

    def visit_Assign (self, node):
        self.generic_visit (node)
        # Assign(targets=[Name(id='a', ctx=Store())], value=Num(n=2))
        for target in node.targets:
            self.known_names[target.id]+= 1
            self.defined_names[self.stack].append (target.id)

        return node

    def visit_Delete (self, node):
        self.generic_visit (node)
        # Delete(targets=[Name(id='foo', ctx=Del())])
        for target in node.targets:
            self.known_names[target.id]-= 1
            self.defined_names[self.stack].remove (target.id)

        return node

    def visit_Call (self, node):
        self.generic_visit (node)
        # Call(func=Name(id='b', ctx=Load()), args=[], keywords=[], starargs=None,
        #      kwargs=None)
        if   type (node.func)==ast.Name:
            func_name= node.func.id
            defs= self.known_names[func_name]
            if defs==0:
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

    def visit_With (self, node):
        # With(items=[withitem(context_expr=Call(func=Name(id='foo', ctx=Load()),
        #                                        args=[], keywords=[], starargs=None,
        #                                        kwargs=None),
        #                      optional_vars=Name(id='bar', ctx=Store()))], body=[Pass()])
        for item in node.items:
            if item.optional_vars is not None:
                self.known_names[item.optional_vars.id]+= 1
                self.defined_names[self.stack].append (item.optional_vars.id)

        self.generic_visit (node)

        # handle 'remote'
        sub_node= node.items[0].context_expr
        if type (sub_node)==Call and sub_node.func.id=='remote':
            # capture the body and put it as the first argument to ssh()
            # but within a module, and already pickled;
            # otherwise we need to create an AST for the call of all the
            # constructors in the body we capture... it's complicated
            m= Module (body=node.body)

            data= pickle.dumps (m)
            s= Bytes (s=data)
            s.lineno= node.lineno
            s.col_offset= node.col_offset
            sub_node.args.insert (0, s)

            p= Pass ()
            p.lineno= node.lineno+1
            p.col_offset= node.col_offset+4

            node.body= [ p ]

        return node
