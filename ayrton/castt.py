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
from ast import Pass, Module, Bytes, copy_location, Call, Name, Load, Str, BitOr
from ast import fix_missing_locations, Import, alias, Attribute, ImportFrom
from ast import keyword, Gt, Lt, GtE, RShift, Tuple, FunctionDef, arguments
from ast import Store, Assign, Subscript, NameConstant
import pickle
from collections import defaultdict
import logging

logger= logging.getLogger ('ayrton.castt')

import ayrton
from ayrton.ast_pprinter import pprint

def append_to_tuple (t, o):
    l= list (t)
    l.append (o)
    return tuple (l)

def pop_from_tuple (t, n=-1):
    l= list (t)
    l.pop (n)
    return tuple (l)

def is_executable (node):
    # Call(func=Call(func=Name(id='Command', ctx=Load()),
    #                args=[Str(s='ls')], keywords=[], starargs=None, kwargs=None),
    #      args=[Str(s='-l')], keywords=[], starargs=None, kwargs=None)
    return (type (node)==Call and
            type (node.func)==Call and
            type (node.func.func)==Name and
            node.func.func.id=='Command')

def is_option (arg):
    return type (arg)==Call and type (arg.func)==Name and arg.func.id=='o'

def has_keyword (node, keyword):
    return any ([kw.arg==keyword for kw in node.keywords])

def update_keyword (node, keyword):
    found= False
    for i in range (len (node.keywords)):
        if node.keywords[i].arg==keyword.arg:
            # TODO: warn
            node.keywords[i]= keyword
            found= True
            # there can't be two
            break

    if not found:
        node.keywords.append (keyword)

def func_name2dotted_exec (node):
    logger.debug (ast.dump (node))

    complete_name= str (pprint (node))

    while type (node) in (Attribute, Subscript, Call):
        if type (node) in (Attribute, Subscript):
            node= node.value
        elif type (node) in (Call, ):
            node= node.func

    if type (node)==Name:
        return (node.id, complete_name)
    else:
        return (None, None)


class CrazyASTTransformer (ast.NodeTransformer):
    def __init__ (self, environ, file_name=None):
        super ().__init__ ()
        # the whole ayrton instace globals
        self.environ= environ
        # names defined in the global namespace
        self.known_names= defaultdict (lambda: 0)
        # holds the names in the stack so far
        # NOTE: it must be a tuple so it can be hashable
        self.stack= ()
        # holds the temporary namespaces in function and class definitions
        # key: the stack so far
        # value: list of names
        self.defined_names= defaultdict (list)
        # for testing
        self.seen_names= set ()
        self.file_name= file_name

    def modify (self, tree):
        m= self.visit (tree)
        ast.fix_missing_locations (m)

        return m

    # The following constructs bind names:
    # [x] formal parameters to functions,
    # [x] import statements,
    # [x] class and
    # [x] function definitions (these bind the class or function name
    #     in the defining block),
    # [x] and targets that are identifiers if occurring in an assignment,
    # [x] for loop header, or
    # [x] after as in a with statement
    # [x] or except clause.
    # The import statement of the form from ... import * binds all names defined
    # in the imported module, except those beginning with an underscore.

    # A block is a piece of Python program text that is executed as a unit.
    # The following are blocks:
    # [x] a module,
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

    def bind (self, o):
        name= None

        if type (o)==Name:
            # Name(id='a', ctx=Store())
            name= o.id

        elif type (o)==str:
            # NOTE: when?
            name= o

        elif type (o)==Tuple:
            # Tuple(elts=[Name(id='a', ctx=Store()), Name(id='b', ctx=Store())])
            for elt in o.elts:
                self.bind (elt)

        elif type (o)==list:
            for e in o:
                self.bind (e)

        if name is not None:
            logger.debug ('binding "%s"', name)
            self.known_names[name]+= 1
            self.defined_names[self.stack].append (name)
            self.seen_names.add (name)

    def unbind (self, name, remove_from_stack=False):
        logger.debug ('unbinding "%s"', name)
        self.known_names[name]-= 1
        if remove_from_stack:
            self.defined_names[self.stack].remove (name)

    def visit_Import (self, node):
        self.generic_visit (node)
        # Import(names=[alias(name='foo', asname=None)])
        for name in node.names:
            if name.asname is not None:
                n= name.asname
            else:
                # 'import os.path' -> only save 'os'
                # NOTE: why? doesn't this clash with resolving foo.py as executable name?
                n= name.name.split ('.')[0]

            logger.debug (n)
            self.bind (n)

        return node

    visit_ImportFrom= visit_Import
        # ImportFrom(module='bar', names=[alias(name='baz', asname=None)], level=0)

    def visit_ClassDef (self, node):
        # ClassDef(name='foo', bases=[], keywords=[], starargs=None, kwargs=None,
        #          body=[Pass()], decorator_list=[])
        self.bind (node.name)

        self.stack= append_to_tuple (self.stack, node.name)
        self.generic_visit (node)

        # take out the function from the stack
        names= self.defined_names[self.stack]
        self.stack= pop_from_tuple (self.stack)
        # ... and unbind the names defined in it from the known_names
        for name in names:
            self.unbind (name)

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

        # add the name as local name
        self.bind (node.name)

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
            self.unbind (name)

        return node

    visit_AsyncFunctionDef= visit_FunctionDef

    def visit_For (self, node):
        # For(target=Name(id='x', ctx=Store()), iter=List(elts=[], ctx=Load()),
        #     body=[Pass()], orelse=[])
        # For(target=Tuple(elts=[Name(id='band', ctx=Store()), Name(id='color', ctx=Store())], ctx=Store()),
        #     iter=Tuple(elts=[...], ctx=Load()),
        #     body=[Pass()], orelse=[])
        self.bind (node.target)
        self.generic_visit (node)

        # if iter is Command, set _out=Capture
        # so this works as expected:
        # for line in ls(): ...

        # For(target=Name(id='line', ctx=Store()),
        #     iter=Call(func=Call(func=Name(id='Command', ctx=Load()), ...
        if is_executable (node.iter):
            update_keyword (node.iter,
                            keyword (arg='_out', value=Name (id='Capture', ctx=Load ())))
            update_keyword (node.iter,
                            keyword (arg='_bg', value=NameConstant (value=True)))

        return node

    visit_AsyncFor= visit_For

    def visit_ExceptHandler (self, node):
        # ExceptHandler(type=Name(id='A', ctx=Load()),
        #               name='e',
        #               body=[Pass()])
        self.bind (node.name)
        self.generic_visit (node)

        return node

    def visit_Assign (self, node):
        # Assign(targets=[Tuple(elts=[Name(id='a', ctx=Store()), Name(id='b', ctx=Store())], ctx=Store())],
        #        value=Tuple(elts=[Num(n=4), Num(n=2)], ctx=Load()))
        self.generic_visit (node)
        self.bind (node.targets)

        return node

    def visit_Delete (self, node):
        self.generic_visit (node)
        # Delete(targets=[Name(id='foo', ctx=Del())])
        for name in node.targets:
            self.unbind (name.id, remove_from_stack=True)

        return node

    # BinOp(left=BinOp(left=Name(id='a', ctx=Load()),
    #                  op=BitOr(), right=Name(id='b', ctx=Load())),
    #       op=BitOr(), right=Name(id='c', ctx=Load()))
    def visit_BinOp (self, node):
        self.generic_visit (node)

        # BinOp( left=Call(...), op=BitOr(), right=Call(...))
        if type (node.op)==BitOr:
            # pipe
            # BinOp (left, BitOr, right) -> right (left, ...)

            # check the left and right; if they're calls to Command
            # then do the magic

            # NOTE: they're Commands only because the children have already been
            # visited and transformed to such things

            both= is_executable (node.left) and is_executable (node.right)

            if both:
                # left (...) | right (...)

                # r, w= os.pipe ()
                # left (..., _out=w)
                # os.close (w)
                # right (..., _in=r)
                # os.close (r)

                # Assign(targets=[Tuple(elts=[Name(id='r', ctx=Store()),
                #                             Name(id='w', ctx=Store())], ctx=Store())],
                #        value=Call(func=Attribute(value=Name(id='os', ctx=Load()),
                #                                  attr='pipe', ctx=Load()),
                #                   args=[], keywords=[], starargs=None, kwargs=None)),
                # Expr(value=Call(func=Name(id='echo', ctx=Load()),
                #                 args=[Str(s='pipe!')],
                #                 keywords=[keyword(arg='_out', value=Name(id='w', ctx=Load()))],
                #                 starargs=None, kwargs=None)),
                # Expr(value=Call(func=Attribute(value=Name(id='os', ctx=Load()), attr='close', ctx=Load()),
                #                 args=[Name(id='w', ctx=Load())],
                #                 keywords=[], starargs=None, kwargs=None)),
                # Expr(value=Call(func=Name(id='grep', ctx=Load()),
                #                 args=[Str(s='pipe')],
                #                 keywords=[keyword(arg='_in', value=Name(id='r', ctx=Load()))],
                #                 starargs=None, kwargs=None)),
                # Expr(value=Call(func=Attribute(value=Name(id='os', ctx=Load()), attr='close', ctx=Load()),
                #                 args=[Name(id='r', ctx=Load())],
                #                 keywords=[], starargs=None, kwargs=None))

                # I can't believe it's this easy
                # TODO: check if _err is not being captured instead
                # TODO: warn about keywords being rewritten
                update_keyword (node.left,
                                keyword (arg='_out', value=Name (id='Pipe', ctx=Load ())))
                update_keyword (node.left,
                                keyword (arg='_bg',  value=Name (id='True', ctx=Load ())))
                ast.fix_missing_locations (node.left)
                update_keyword (node.right, keyword (arg='_in', value=node.left))
                node= node.right

                # Call(func=Call(func=Attribute(value=Name(id='CommandWrapper', ctx=Load()),
                #                               attr='_create', ctx=Load()),
                #                args=[Str(s='grep')], keywords=[], starargs=None, kwargs=None),
                #      args=[Call(func=Call(func=Attribute(value=Name(id='CommandWrapper', ctx=Load()),
                #                                          attr='_create', ctx=Load()),
                #                      args=[Str(s='ls')], keywords=[], starargs=None, kwargs=None),
                #                 args=[], keywords=[keyword(arg='_out',
                #                                            value=Name(id='Capture', ctx=Load()))],
                #                 starargs=None, kwargs=None),
                #            Str(s='foo')],
                #      keywords=[], starargs=None, kwargs=None)

        elif type (node.op)==RShift:
            # BinOp(left=Call(func=Name(id='ls', ctx=Load()), args=[], keywords=[], starargs=None, kwargs=None),
            #       op=RShift(),
            #       right=Str(s='foo.txt'))
            if is_executable (node.left):
                update_keyword (node.left,
                                keyword (arg='_out',
                                         value=Call (func=Name (id='open', ctx=Load ()),
                                                     args=[node.right, Str (s='ab')],
                                                     keywords=[])))
                ast.fix_missing_locations (node.left)
                node= node.left

        return node

    # Compare(left=Call(func=Name(id='grep', ctx=Load()), args=[Str(s='root')], keywords=[], starargs=None, kwargs=None),
    #        ops=[Lt()],
    #        comparators=[BinOp(left=Str(s='/etc/passwd'),
    #                           op=RShift(),
    #                           right=Str(s='/tmp/foo'))])
    def visit_Compare (self, node):
        self.generic_visit (node)
        ans= node

        # ls () < "bar.txt" > "foo.txt"
        # Compare(left=Call(func=Name(id='ls', ctx=Load()), args=[], keywords=[],
        #                        starargs=None, kwargs=None),
        #         ops=[Lt(), Gt()],
        #         comparators=[Str(s='bar.txt'), Str(s='foo.txt')]))

        if is_executable (node.left):
            # yes, they're reversed, but it makes more sense to me like this
            for comp, op in zip (node.ops, node.comparators):
                if type (comp)==Gt:
                    # > means _out
                    update_keyword (node.left, keyword (arg='_out', value=op))
                    ans= node.left
                elif type (comp)==GtE:
                    # >= means _out+_err
                    update_keyword (node.left, keyword (arg='_out', value=op))
                    update_keyword (node.left, keyword (arg='_err_to_out', value=op))
                    ans= node.left
                elif type (comp)==Lt:
                    # < means _in
                    update_keyword (node.left, keyword (arg='_in', value=op))
                    ans= node.left

        return ans

    def visit_Call (self, node):
        self.generic_visit (node)
        # Call(func=Name(id='b', ctx=Load()), args=[], keywords=[], starargs=None,
        #      kwargs=None)
        # Call(func=Attribute(value=Name(id='test', ctx=Load()), attr='py', ctx=Load()), ...)
        # NOTE: what other things can be the func part?
        name= None
        unknown= False

        if type (node.func)==Name:
            name= func_name= node.func.id
            defs= self.known_names[func_name]
            if defs==0:
                unknown= True

        elif type (node.func)==Attribute:
            name, func_name= func_name2dotted_exec (node.func)
            # node.func is not completely formed by Names
            # so leave it alone
            if name is None:
                return node

            defs= self.known_names[name]
            if defs==0:
                unknown= True

        logger.debug2 ("%s: %s", name, unknown)

        if unknown:
            if not name in self.environ:
                # it's not one of the builtin functions
                # I guess I have no other option but to try to execute
                # something here...
                new_node= Call (func=Name (id='Command', ctx=Load ()),
                                args=[Str (s=func_name)], keywords=[])

                # check if the first parameter is a Command; if so, redirect
                # its output, remove it from the args and put it in the _in
                # kwarg
                if len (node.args)>0:
                    first_arg= node.args[0]
                    if is_executable (first_arg) and not has_keyword (first_arg, '_err'):
                        out= keyword (arg='_out', value=Name (id='Pipe', ctx=Load ()))
                        update_keyword (first_arg, out)
                        bg= keyword (arg='_bg', value=Name (id='True', ctx=Load ()))
                        update_keyword (first_arg, bg)
                        node.args.pop (0)
                        update_keyword (node, keyword (arg='_in', value=first_arg))

                    for arg in node.args:
                        if is_option (arg):
                            # ast_pprinter takes care of expressions
                            kw= arg.keywords[0]
                            logger.debug2 ("->>>kw: %s", ast.dump (kw))
                            kw.arg= str (pprint (kw.arg))

                ast.copy_location (new_node, node)
                node.func= new_node
                ast.fix_missing_locations (node)
            else:
                # this is a normal function call
                # Call(func=Name(id='foo', ctx=Load()),
                #      args=[Call(func=Name(id='o', ctx=Load()),
                #                 args=[], keywords=[keyword(arg='a', value=Num(n=42))],
                #                 starargs=None, kwargs=None)],
                #      keywords=[], starargs=None, kwargs=None))
                # the parser has converted all the keyword arguments to o(k=v)
                # we need to convert them back to keywords and apply Python's syntax rules
                new_args= []
                used_keywords= set ()
                first_kw= False
                for index, arg in enumerate (node.args):
                    # NOTE: maybe o() can be left in its own namespace so it doesn't pollute
                    if is_option (arg):
                        kw_expr= arg.keywords[0].arg
                        if not isinstance (kw_expr, ast.Name) and not isinstance (kw_expr, str):
                            raise SyntaxError (self.file_name, node.lineno, node.col_offset,
                                               "keyword can't be an expression")

                        if isinstance (kw_expr, ast.Name):
                            kw_name= kw_expr.id
                        else:
                            kw_name= kw_expr  # str

                        if kw_name in used_keywords:
                            raise SyntaxError (self.file_name, node.lineno, node.col_offset,
                                               "keyword argument repeated")

                        # convert the expr into a str
                        new_kw= keyword (kw_name, arg.keywords[0].value)
                        node.keywords.append (new_kw)
                        used_keywords.add (kw_name)
                        first_kw= True
                    else:
                        if first_kw:
                            raise SyntaxError (self.file_name, node.lineno, node.col_offset,
                                               "non-keyword arg after keyword arg")

                        new_args.append (arg)

                node.args= new_args

        return node

    def visit_With (self, node):
        # With(items=[withitem(context_expr=Call(func=Name(id='foo', ctx=Load()),
        #                                        args=[], keywords=[], starargs=None,
        #                                        kwargs=None),
        #                      optional_vars=Name(id='bar', ctx=Store()))], body=[Pass()])
        for item in node.items:
            if item.optional_vars is not None:
                self.bind (item.optional_vars.id)

        self.generic_visit (node)

        # handle 'remote'
        sub_node= node.items[0].context_expr
        if (type (sub_node)==Call and hasattr (sub_node.func, 'id') and
            sub_node.func.id=='remote'):
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

    visit_AsyncWith= visit_With
