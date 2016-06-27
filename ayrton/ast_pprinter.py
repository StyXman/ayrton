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

from ast import Module, ImportFrom, Expr, Call, Name, FunctionDef, Assign, Str
from ast import dump, If, Compare, Eq, For, Attribute, Gt, Num, IsNot, BinOp
from ast import NameConstant, Mult, Add, Import, List, Dict, Is, BoolOp, And
from ast import Subscript, Index, Tuple, Lt, Sub, Global, Return, AugAssign
from ast import While, UnaryOp, Not, ClassDef, Mod, Yield, NotEq, Try, Pass
from ast import ExceptHandler, Break, Slice, USub, ListComp, In, Lambda, BitAnd
from ast import BitOr, Or, Delete, Bytes, Raise, NotIn, RShift, GeneratorExp
from ast import Assert, Set, SetComp, LtE, IfExp, FloorDiv, GtE, With, Continue
from ast import YieldFrom, UAdd, LShift, DictComp, Div, Starred, BitXor, Pow
from _ast import arguments, arg as arg_type, keyword as keyword_type
from _ast import alias as alias_type, comprehension, withitem
from _ast import AsyncFor, AsyncFunctionDef, AsyncWith, Await, Starred

import logging
logger= logging.getLogger ('ayrton.ast_pprint')

class pprint:
    """Lazy pprinter that only does something when converted to string"""
    def __init__ (self, node):
        self.node= node

    def pprint_body (self, body, level):
        for statement in body:
            yield '    '*level
            yield from self.pprint_inner (statement, level)
            yield '\n'

    def pprint_seq (self, seq, sep=', '):
        for index, elem in enumerate (seq):
            if type (elem)==str:
                yield elem
            else:
                yield from self.pprint_inner (elem)

            if index<len (seq)-1:
                if type (sep)==str:
                    yield sep
                else:
                    yield from self.pprint_inner (sep)

    def pprint_orelse (self, orelse, level):
        if len (orelse)>0:
            yield '    '*level+'else:\n'
            yield from self.pprint_body (orelse, level+1)

    def pprint_args (self, args, defaults):
        # TODO: anotations
        # args=[arg(arg='a', annotation=None), arg(arg='b', annotation=None)]
        # defaults=[Num(n=1)]
        d_index= len (args)-len (defaults)
        for index, arg in enumerate (args):
            yield arg.arg

            if index>=d_index:
                yield '='
                yield from self.pprint_inner (defaults[index-d_index])

            if index<len (args)-1:
                yield ', '

    def __str__ (self):
        data= list (self.pprint_inner (self.node, 0))
        logger.debug2 (data)
        return ''.join (data)

    def pprint_inner (self, node, level=0):
        t= type (node)

        if t==Add:
            yield '+'

        elif t==And:
            yield ' and '

        elif t==Assert:
            # Assert(test=..., msg=None)
            yield 'assert '
            yield from self.pprint_inner (node.test)
            # TODO: msg

        elif t==Assign:
            # Assign(targets=[Name(id='c', ctx=Store())],
            #        value=...)
            yield from self.pprint_seq (node.targets)
            yield '= '
            yield from self.pprint_inner (node.value)

        elif t==AsyncFor:
            yield 'async '
            # For(target=..., iter=..., body=[...], orelse=[...])
            node= For (target=node.target, iter=node.iter, body=node.body, orelse=node.orelse)
            yield from self.pprint_inner (node)

        elif t==AsyncFunctionDef:
            yield 'async '
            # FunctionDef(name='foo', args=arguments(...), body=[ ... ], decorator_list=[], returns=None)
            node= FunctionDef (name=node.name, args=node.args, body=node.body, decorator_list=node.decorator_list,
                               returns=node.returns)
            yield from self.pprint_inner (node)

        elif t==AsyncWith:
            yield 'async '
            # With(items=[...], body=[...])
            node= With (items=node.items, body=node.body)
            yield from self.pprint_inner (node)

        elif t==Attribute:
            # Attribute(value=Name(id='node', ctx=Load()), attr='body', ctx=Load())
            yield from self.pprint_inner (node.value)
            yield '.'
            yield node.attr

        elif t==AugAssign:
            # AugAssign(target=Name(id='ans', ctx=Store()), op=Add(), value=Name(id='a', ctx=Load()))
            yield from self.pprint_inner (node.target)
            yield from self.pprint_inner (node.op)
            yield '= '
            yield from self.pprint_inner (node.value)

        elif t==Await:
            # value=Await(value=...)
            yield 'await '
            yield from self.pprint_inner (node.value)

        elif t==BinOp:
            # BUG: 5*(3+4) -> '5*3+4'
            # do not surround by parenthesis
            # because it breaks part of the code that (ab) uses this to rebuild
            # option and executable names
            # yield '('
            yield from self.pprint_inner (node.left)
            yield from self.pprint_inner (node.op)
            yield from self.pprint_inner (node.right)
            # yield ')'

        elif t==BitAnd:
            yield ' & '

        elif t==BitOr:
            yield '|'

        elif t==BitXor:
            yield '^'

        elif t==BoolOp:
            self.pprint_seq (node.values, node.op)

        elif t==Break:
            yield 'break'

        elif t==Bytes:
            yield repr (node.s)

        elif t==Call:
            # Call(func=Name(id='foo', ctx=Load()), args=[], keywords=[])
            # Call(func=Name(id='foo', ctx=Load()),
            #      args=[Num(n=1), Starred(value=Name(id='bar', ctx=Load()), ctx=Load())],
            #      keywords=[keyword(arg='a', value=Num(n=3)),
            #                keyword(arg=None, value=Name(id='baz', ctx=Load()))]))
            # TODO: annotations
            yield from self.pprint_inner (node.func)
            yield ' ('
            yield from self.pprint_seq (node.args)

            if len (node.args)>0 and len (node.keywords)>0:
                yield ', '

            yield from self.pprint_seq (node.keywords)
            yield ')'

        elif t==ClassDef:
            # ClassDef(name='ToExpand', bases=[Name(id='object', ctx=Load())],
            #          keywords=[], starargs=None, kwargs=None, body=[...]
            yield 'class '
            yield node.name

            # TODO: more
            if len (node.bases)>0:
                yield ' ('
                yield from self.pprint_seq (node.bases)
                yield ')'

            yield ':'
            yield from self.pprint_body (node.body, level+1)

        elif t==Compare:
            # Compare(left=Name(id='t', ctx=Load()), ops=[Eq()], comparators=[Name(id='Module', ctx=Load())])
            # TODO: do properly
            yield from self.pprint_inner (node.left)
            for op in node.ops:
                yield from self.pprint_inner (op)

            for comparator in node.comparators:
                yield from self.pprint_inner (comparator)

        elif t==Continue:
            yield 'continue'

        elif t==Delete:
            yield 'delete '
            yield from self.pprint_seq (node.targets)

        elif t==Dict:
            yield '{ '
            for k, v in zip (node.keys, node.values):
                yield from self.pprint_inner (k)
                yield '='
                yield from self.pprint_inner (v)
                yield ', '
            yield ' }'

        elif t==DictComp:
            # DictComp(key=Name(id='v', ctx=Load()), value=Name(id='k', ctx=Load()), generators=[comprehension(target=Tuple(elts=[Name(id='k', ctx=Store()), Name(id='v', ctx=Store())], ctx=Store()), iter=Call(func=Name(id='enumerate', ctx=Load()), args=[Name(id='_b32alphabet', ctx=Load())], keywords=[], starargs=None, kwargs=None), ifs=[])])
            yield '{ '
            yield from self.pprint_inner (node.key)
            yield ': '
            yield from self.pprint_inner (node.value)
            yield ' for '
            # TODO: more
            yield from self.pprint_inner (node.generators[0])
            yield ' }'

        elif t==Div:
            yield '/'

        elif t==Eq:
            yield '=='

        elif t==ExceptHandler:
            # ExceptHandler(type=Name(id='KeyError', ctx=Load()), name=None, body=[Pass()])
            yield '    '*level+'except '
            if node.type is not None:
                yield from self.pprint_inner (node.type)
                if node.name is not None:
                    yield ' as '
                    yield node.name

            yield ':\n'
            yield from self.pprint_body (node.body, level+1)

        elif t==Expr:
            # Expr(value=...)
            yield from self.pprint_inner (node.value, level)

        elif t==FloorDiv:
            yield '\\\\'

        elif t==For:
            # For(target=..., iter=..., body=[...], orelse=[...])
            yield 'for '
            yield from self.pprint_inner (node.target)
            yield ' in '
            yield from self.pprint_inner (node.iter)
            yield ':\n'
            yield from self.pprint_body (node.body, level+1)
            yield from self.pprint_orelse (node.orelse, level)

        elif t==FunctionDef:
            # FunctionDef(name='foo', args=arguments(...), body=[ ... ], decorator_list=[], returns=None)
            # TODO: decorator_list
            # TODO: returns
            yield 'def '
            yield node.name
            yield ' ('
            yield from self.pprint_inner (node.args)
            yield '):\n'
            yield from self.pprint_body (node.body, level+1)

        elif t==GeneratorExp:
            # GeneratorExp(elt=Name(id='line', ctx=Load()), generators=[...])
            yield '( '
            yield from self.pprint_inner (node.elt)
            yield ' for '
            # TODO: more
            yield from self.pprint_inner (node.generators[0])
            yield ' )'

        elif t==Global:
            yield 'global '
            yield from self.pprint_seq (node.names)

        elif t==Gt:
            yield '>'

        elif t==GtE:
            yield '>='

        elif t==If:
            # If(test=..., body=[...], orelse=[...]
            yield 'if '
            yield from self.pprint_inner (node.test)
            yield ':\n'
            yield from self.pprint_body (node.body, level+1)

            if len (node.orelse)>0:
                # special case for elif
                if len (node.orelse)==1 and type (node.orelse[0])==If:
                    yield '    '*level+'el'
                    yield from self.pprint_inner (node.orelse[0], level)
                else:
                    yield from self.pprint_orelse (node.orelse, level)

        elif t==IfExp:
            # IfExp(test=..., body=Str(s=''), orelse=Str(s='s'))
            yield from self.pprint_inner (node.body)
            yield ' if '
            yield from self.pprint_inner (node.test)
            yield ' else '
            yield from self.pprint_inner (node.orelse)

        elif t==Import:
            # Import(names=[alias(name='ayrton', asname=None)])
            yield "import "
            yield from self.pprint_seq (node.names)

        elif t==ImportFrom:
            # ImportFrom(module='ayrton.execute', names=[alias(name='Command', asname=None)], level=0)
            yield "from "
            yield node.module
            yield " import "
            yield from self.pprint_seq (node.names)

        elif t==In:
            yield ' in '

        elif t==Index:
            yield from self.pprint_inner (node.value)

        elif t==Is:
            yield ' is '

        elif t==IsNot:
            yield ' is not '

        elif t==LShift:
            yield '<<'

        elif t==Lambda:
            # Lambda(args=arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=Num(n=0))
            yield 'lambda '
            yield from self.pprint_inner (node.args)
            yield ': '
            yield from self.pprint_inner (node.body)

        elif t==List:
            yield '[ '
            yield from self.pprint_seq (node.elts)
            yield ' ]'

        elif t==ListComp:
            # ListComp(elt=Name(id='i', ctx=Load()), generators=[...])
            # [ i for i in self.indexes if i.right is not None ]
            yield '[ '
            yield from self.pprint_inner (node.elt)
            yield ' for '
            # TODO: more
            yield from self.pprint_inner (node.generators[0])
            yield ' ]'

        elif t==Lt:
            yield '<'

        elif t==LtE:
            yield '<='

        elif t==Mod:
            yield ' % '

        elif t==Module:
            # Module(body=[ ... ])
            yield from self.pprint_body (node.body, 0)

        elif t==Mult:
            yield '*'

        elif t==Name:
            yield node.id

        elif t==NameConstant:
            yield str (node.value)

        elif t==Not:
            yield 'not '

        elif t==NotEq:
            yield '!='

        elif t==NotIn:
            yield ' not in '

        elif t==Num:
            yield str (node.n)

        elif t==Or:
            yield ' or '

        elif t==Pass:
            yield 'pass\n'

        elif t==Pow:
            yield '**'

        elif t==RShift:
            yield '>>'

        elif t==Raise:
            # Raise(exc=Call(func=Name(id='ValueError', ctx=Load()),
            #                args=[Str(s='too many lines')], keywords=[],
            #                starargs=None, kwargs=None),
            #       cause=None)
            yield 'raise '
            if node.exc is not None:
                yield from self.pprint_inner (node.exc)
            # TODO: cause?

        elif t==Return:
            yield 'return '
            if node.value is not None:
                yield from self.pprint_inner (node.value)

        elif t==Set:
            yield '{ '
            self.pprint_seq (node.elts)
            yield ' }'

        elif t==SetComp:
            # SetComp(elt=Name(id='name', ctx=Load()), generators=[...])
            yield '{ '
            yield from self.pprint_inner (node.elt)
            yield ' for '
            # TODO: more
            yield from self.pprint_inner (node.generators[0])

        elif t==Slice:
            # Slice(lower=None, upper=Name(id='left_cb', ctx=Load()), step=None)
            if node.lower is not None:
                yield from self.pprint_inner (node.lower)

            yield ':'

            if node.upper is not None:
                yield from self.pprint_inner (node.upper)

            if node.step is not None:
                yield ':'
                yield from self.pprint_inner (node.step)

        elif t==Starred:
            # Starred(value=Name(id='bar', ctx=Load()), ctx=Load())
            yield '*'
            yield from self.pprint_inner (node.value)

        elif t==Str:
            # Str(s='true')
            yield repr (node.s)

        elif t==Sub:
            yield '-'

        elif t==Subscript:
            # Subscript(value=Attribute(value=Name(id='node', ctx=Load()), attr='orelse', ctx=Load()),
            #           slice=Index(value=Num(n=0)), ctx=Load())
            yield from self.pprint_inner (node.value)
            yield '['
            yield from self.pprint_inner (node.slice)
            yield ']'

        elif t==Try:
            # Try(body=[...],  handlers=[...], orelse=[], finalbody=[])
            yield 'try:\n'
            yield from self.pprint_body (node.body, level+1)
            if len (node.handlers)>0:
                for handler in node.handlers:
                    yield from self.pprint_inner (handler, level)

            yield from self.pprint_orelse (node.orelse, level)
            if len (node.finalbody)>0:
                yield '    '*level+'finally:\n'
                yield from self.pprint_body (node.finalbody, level+1)

        elif t==Tuple:
            yield '( '
            yield from self.pprint_seq (node.elts)
            yield ' )'

        elif t==UAdd:
            yield '+'

        elif t==USub:
            yield '-'

        elif t==UnaryOp:
            yield from self.pprint_inner (node.op)
            yield from self.pprint_inner (node.operand)

        elif t==While:
            yield 'while '
            yield from self.pprint_inner (node.test)
            yield ':\n'
            yield from self.pprint_body (node.body, level+1)
            yield from self.pprint_orelse (node.orelse, level)

        elif t==With:
            yield 'with '
            yield from self.pprint_seq (node.items)
            yield ':\n'
            yield from self.pprint_body (node.body, level+1)

        elif t==Yield:
            # Yield(value=Attribute(value=Name(id='self', ctx=Load()), attr='left', ctx=Load()))
            yield 'yield '
            yield from self.pprint_inner (node.value)

        elif t==YieldFrom:
            yield 'yield from '
            yield from self.pprint_inner (node.value)

        elif t==alias_type:
            yield node.name
            if node.asname is not None:
                yield " as "
                yield node.asname

        elif t==arg_type:
            # arg(arg='node', annotation=None)
            # TODO: annotation
            yield node.arg

        elif t==arguments:
            # arguments(args=[arg(arg='a', annotation=None), arg(arg='b', annotation=None)],
            #           vararg=arg(arg='more', annotation=None), kwonlyargs=[], kw_defaults=[],
            #           kwarg=arg(arg='kmore', annotation=None), defaults=[Num(n=1)])

            # this is tricky

            # first there are five, not four, types of arguments
            # positional, positional with default value, extra positional, keywords
            # and extra keywords

            # positional arguments are in args, and the default values in defaults
            # but you have to calculate to which args they belong

            # extra positional is in vararg

            # keyword arguments are in kwonlyargs and the defaults in kw_defaults

            # extra keywords is in kwarg

            yield from self.pprint_args (node.args, node.defaults)

            if len (node.args)>0 and (node.vararg is not None or
                                      len (node.kwonlyargs)>0 or
                                      node.kwarg is not None):
                yield ', '

            if node.vararg is not None:
                yield '*'
                yield from self.pprint_inner (node.vararg)

            if ((len (node.args)>0 or node.vararg is not None) and
                (len (node.kwonlyargs)>0 or node.kwarg is not None)):

                yield ', '

            yield from self.pprint_args (node.kwonlyargs, node.kw_defaults)

            if ((len (node.args)>0 or
                 node.vararg is not None or
                 len (node.kwonlyargs)>0) and node.kwarg is not None):
                yield ', '

            # empty arguments() (from a lambda) do not have this attr (!!!)
            if hasattr (node, 'kwarg') and node.kwarg is not None:
                yield '**'
                yield from self.pprint_inner (node.kwarg)

        elif t==comprehension:
            # comprehension(target=Name(id='i', ctx=Store()),
            #               iter=Attribute(value=Name(id='self', ctx=Load()),
            #                              attr='indexes', ctx=Load()),
            #               ifs=[Compare(left=..., ops=[IsNot()],
            #                            comparators=[NameConstant(value=None)])])
            # i in self.indexes if i.right is not None
            yield from self.pprint_inner (node.target)
            yield ' in '
            yield from self.pprint_inner (node.iter)

            if len (node.ifs)>0:
                # TODO: more
                yield ' if '
                yield from self.pprint_inner (node.ifs[0])

        elif t==keyword_type:
            # keyword(arg='end', value=Str(s=''))
            # keyword(arg=None, value=Name(id='baz', ctx=Load()))]))
            if node.arg is not None:
                yield node.arg
                yield '='
            else:
                yield '**'
            yield from self.pprint_inner (node.value)

        elif t==withitem:
            # withitem(context_expr=..., optional_vars=Name(id='f', ctx=Store()))
            yield from self.pprint_inner (node.context_expr)
            if node.optional_vars is not None:
                yield ' as '
                yield from self.pprint_inner (node.optional_vars)

        elif t==str:
            yield node

        else:
            yield '\n'
            yield '# unknown construction\n'
            yield dump (node)
