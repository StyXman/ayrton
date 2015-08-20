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
try:
    # python3.5 support
    from _ast import AsyncFor, AsyncFunctionDef, AsyncWith, Await
except ImportError:
    AsyncFor= AsyncFunctionDef= AsyncWith= Await= object()

def pprint_body (body, level):
    for statement in body:
        yield '    '*level
        for i in pprint_inner (statement, level): yield i
        yield '\n'

def pprint_seq (seq, sep=', '):
    for index, elem in enumerate (seq):
        if type (elem)==str:
            yield elem
        else:
            for i in pprint_inner (elem): yield i

        if index<len (seq)-1:
            if type (sep)==str:
                yield sep
            else:
                for i in pprint_inner (sep): yield i

def pprint_orelse (orelse, level):
    if len (orelse)>0:
        yield '    '*level+'else:\n'
        for i in pprint_body (orelse, level+1): yield i

def pprint_args (args, defaults):
    # TODO: anotations
    # args=[arg(arg='a', annotation=None), arg(arg='b', annotation=None)]
    # defaults=[Num(n=1)]
    d_index= len (args)-len (defaults)
    for index, arg in enumerate (args):
        yield arg.arg

        if index>=d_index:
            yield '='
            for i in pprint_inner (defaults[index-d_index]): yield i

        if index<len (args)-1:
            yield ', '

def pprint (node, level=0):
    return ''.join (pprint_inner (node, level))

def pprint_inner (node, level=0):
    t= type (node)

    if t==Add:
        yield '+'

    elif t==And:
        yield ' and '

    elif t==Assert:
        # Assert(test=..., msg=None)
        yield 'assert '
        for i in pprint_inner (node.test): yield i
        # TODO: msg

    elif t==Assign:
        # Assign(targets=[Name(id='c', ctx=Store())],
        #        value=...)
        for i in pprint_inner_seq (node.targets): yield i
        yield '= '
        for i in pprint_inner (node.value): yield i

    elif t==AsyncFor:
        yield 'async '
        # For(target=..., iter=..., body=[...], orelse=[...])
        node= For (target=node.target, iter=node.iter, body=node.body, orelse=node.orelse)
        for i in pprint_inner (node): yield i

    elif t==AsyncFunctionDef:
        yield 'async '
        # FunctionDef(name='foo', args=arguments(...), body=[ ... ], decorator_list=[], returns=None)
        node= FunctionDef (name=node.name, args=node.args, body=node.body, decorator_list=node.decorator_list,
                           returns=node.returns)
        for i in pprint_inner (node): yield i

    elif t==AsyncWith:
        yield 'async '
        # With(items=[...], body=[...])
        node= With (items=node.items, body=node.body)
        for i in pprint_inner (node): yield i

    elif t==Attribute:
        # Attribute(value=Name(id='node', ctx=Load()), attr='body', ctx=Load())
        for i in pprint_inner (node.value): yield i
        yield '.'
        yield node.attr

    elif t==AugAssign:
        # AugAssign(target=Name(id='ans', ctx=Store()), op=Add(), value=Name(id='a', ctx=Load()))
        for i in pprint_inner (node.target): yield i
        for i in pprint_inner (node.op): yield i
        yield '= '
        for i in pprint_inner (node.value): yield i

    elif t==Await:
        # value=Await(value=...)
        yield 'await '
        for i in pprint_inner (node.value): yield i

    elif t==BinOp:
        # BUG:
        # m= ast.parse ('5*(3+4)')
        # ayrton.ast_pprinter.pprint (m)
        # 5*3+4
        for i in pprint_inner (node.left): yield i
        for i in pprint_inner (node.op): yield i
        for i in pprint_inner (node.right): yield i

    elif t==BitAnd:
        yield ' & '

    elif t==BitOr:
        yield '|'

    elif t==BitXor:
        yield '^'

    elif t==BoolOp:
        pprint_seq (node.values, node.op)

    elif t==Break:
        yield 'break'

    elif t==Bytes:
        yield repr (node.s)

    elif t==Call:
        # Call(func=Name(id='foo', ctx=Load()), args=[], keywords=[], starargs=None, kwargs=None)
        # TODO: annotations
        for i in pprint_inner (node.func): yield i
        yield ' ('
        for i in pprint_seq (node.args): yield i

        if len (node.args)>0 and (len (node.keywords)>0 or
                                  node.starargs is not None or
                                  node.kwargs is not None):
            yield ', '

        for i in pprint_seq (node.keywords): yield i

        if ((len (node.args)>0 or len (node.keywords)>0) and
            (node.starargs is not None or node.kwargs is not None)):
            yield ', '

        if node.starargs is not None:
            yield '*'
            for i in pprint_inner (node.starargs): yield i

        if ((len (node.args)>0 or
             len (node.keywords)>0 or
             (node.starargs is not None) and node.kwargs is not None)):
            yield ', '

        if node.kwargs is not None:
            yield '**'
            for i in pprint_inner (node.kwargs): yield i

        yield ')'

    elif t==ClassDef:
        # ClassDef(name='ToExpand', bases=[Name(id='object', ctx=Load())],
        #          keywords=[], starargs=None, kwargs=None, body=[...]
        yield 'class '
        yield node.name

        # TODO: more
        if len (node.bases)>0:
            yield ' ('
            for i in pprint_seq (node.bases): yield i
            yield ')'

        yield ':'
        for i in pprint_body (node.body, level+1): yield i

    elif t==Compare:
        # Compare(left=Name(id='t', ctx=Load()), ops=[Eq()], comparators=[Name(id='Module', ctx=Load())])
        # TODO: do properly
        for i in pprint_inner (node.left): yield i
        for op in node.ops:
            for i in pprint_inner (op): yield i

        for comparator in node.comparators:
            for i in pprint_inner (comparator): yield i

    elif t==Continue:
        yield 'continue'

    elif t==Delete:
        yield 'delete '
        for i in pprint_seq (node.targets): yield i

    elif t==Dict:
        yield '{ '
        for k, v in zip (node.keys, node.values):
            for i in pprint_inner (k): yield i
            yield '='
            for i in pprint_inner (v): yield i
            yield ', '
        yield ' }'

    elif t==DictComp:
        # DictComp(key=Name(id='v', ctx=Load()), value=Name(id='k', ctx=Load()), generators=[comprehension(target=Tuple(elts=[Name(id='k', ctx=Store()), Name(id='v', ctx=Store())], ctx=Store()), iter=Call(func=Name(id='enumerate', ctx=Load()), args=[Name(id='_b32alphabet', ctx=Load())], keywords=[], starargs=None, kwargs=None), ifs=[])])
        yield '{ '
        for i in pprint_inner (node.key): yield i
        yield ': '
        for i in pprint_inner (node.value): yield i
        yield ' for '
        # TODO: more
        for i in pprint_inner (node.generators[0]): yield i
        yield ' }'

    elif t==Div:
        yield '/'

    elif t==Eq:
        yield '=='

    elif t==ExceptHandler:
        # ExceptHandler(type=Name(id='KeyError', ctx=Load()), name=None, body=[Pass()])
        yield '    '*level+'except '
        if node.type is not None:
            for i in pprint_inner (node.type): yield i
            if node.name is not None:
                yield ' as '
                yield node.name

        yield ':'
        for i in pprint_body (node.body, level+1): yield i

    elif t==Expr:
        # Expr(value=...)
        for i in pprint_inner (node.value, level): yield i

    elif t==FloorDiv:
        yield '\\\\'

    elif t==For:
        # For(target=..., iter=..., body=[...], orelse=[...])
        yield 'for '
        for i in pprint_inner (node.target): yield i
        yield ' in '
        for i in pprint_inner (node.iter): yield i
        yield ':\n'
        for i in pprint_body (node.body, level+1): yield i
        for i in pprint_orelse (node.orelse, level): yield i

    elif t==FunctionDef:
        # FunctionDef(name='foo', args=arguments(...), body=[ ... ], decorator_list=[], returns=None)
        # TODO: decorator_list
        # TODO: returns
        yield 'def ', node.name, ' ('
        for i in pprint_inner (node.args): yield i
        yield '):\n'
        for i in pprint_body (node.body, level+1): yield i

    elif t==GeneratorExp:
        # GeneratorExp(elt=Name(id='line', ctx=Load()), generators=[...])
        yield '( '
        for i in pprint_inner (node.elt): yield i
        yield ' for '
        # TODO: more
        for i in pprint_inner (node.generators[0]): yield i
        yield ' )'

    elif t==Global:
        yield 'global '
        for i in pprint_seq (node.names): yield i

    elif t==Gt:
        yield '>'

    elif t==GtE:
        yield '>='

    elif t==If:
        # If(test=..., body=[...], orelse=[...]
        yield 'if '
        for i in pprint_inner (node.test): yield i
        yield ':\n'
        for i in pprint_body (node.body, level+1): yield i

        if len (node.orelse)>0:
            # special case for elif
            if len (node.orelse)==1 and type (node.orelse[0])==If:
                yield '    '*level+'el'
                for i in pprint_inner (node.orelse[0], level): yield i
            else:
                for i in pprint_orelse (node.orelse, level): yield i

    elif t==IfExp:
        # IfExp(test=..., body=Str(s=''), orelse=Str(s='s'))
        for i in pprint_inner (node.body): yield i
        yield ' if '
        for i in pprint_inner (node.test): yield i
        yield ' else '
        for i in pprint_inner (node.orelse): yield i

    elif t==Import:
        # Import(names=[alias(name='ayrton', asname=None)])
        yield "import "
        for i in pprint_seq (node.names): yield i

    elif t==ImportFrom:
        # ImportFrom(module='ayrton.execute', names=[alias(name='Command', asname=None)], level=0)
        yield "from "
        yield node.module
        yield " import "
        for i in pprint_seq (node.names): yield i

    elif t==In:
        yield ' in '

    elif t==Index:
        for i in pprint_inner (node.value): yield i

    elif t==Is:
        yield ' is '

    elif t==IsNot:
        yield ' is not '

    elif t==LShift:
        yield '<<'

    elif t==Lambda:
        # Lambda(args=arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=Num(n=0))
        yield 'lambda '
        for i in pprint_inner (node.args): yield i
        yield ': '
        for i in pprint_inner (node.body): yield i

    elif t==List:
        yield '[ '
        for i in pprint_seq (node.elts): yield i
        yield ' ]'

    elif t==ListComp:
        # ListComp(elt=Name(id='i', ctx=Load()), generators=[...])
        # [ i for i in self.indexes if i.right is not None ]
        yield '[ '
        for i in pprint_inner (node.elt): yield i
        yield ' for '
        # TODO: more
        for i in pprint_inner (node.generators[0]): yield i
        yield ' ]'

    elif t==Lt:
        yield '<'

    elif t==LtE:
        yield '<='

    elif t==Mod:
        yield ' % '

    elif t==Module:
        # Module(body=[ ... ])
        for i in pprint_body (node.body, 0): yield i

    elif t==Mult:
        yield '*'

    elif t==Name:
        yield node.id

    elif t==NameConstant:
        yield node.value

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
            for i in pprint_inner (node.exc): yield i
        # TODO: cause?

    elif t==Return:
        yield 'return '
        if node.value is not None:
            for i in pprint_inner (node.value): yield i

    elif t==Set:
        yield '{ '
        pprint_seq (node.elts)
        yield ' }'

    elif t==SetComp:
        # SetComp(elt=Name(id='name', ctx=Load()), generators=[...])
        yield '{ '
        for i in pprint_inner (node.elt): yield i
        yield ' for '
        # TODO: more
        for i in pprint_inner (node.generators[0]): yield i

    elif t==Slice:
        # Slice(lower=None, upper=Name(id='left_cb', ctx=Load()), step=None)
        if node.lower is not None:
            for i in pprint_inner (node.lower): yield i

        yield ':'

        if node.upper is not None:
            for i in pprint_inner (node.upper): yield i

        if node.step is not None:
            yield ':'
            for i in pprint_inner (node.step): yield i

    elif t==Str:
        # Str(s='true')
        yield repr (node.s)

    elif t==Sub:
        yield '-'

    elif t==Subscript:
        # Subscript(value=Attribute(value=Name(id='node', ctx=Load()), attr='orelse', ctx=Load()),
        #           slice=Index(value=Num(n=0)), ctx=Load())
        for i in pprint_inner (node.value): yield i
        yield '['
        for i in pprint_inner (node.slice): yield i
        yield ']'

    elif t==Try:
        # Try(body=[...],  handlers=[...], orelse=[], finalbody=[])
        yield 'try:\n'
        pprint_body (node.body, level+1)
        if len (node.handlers)>0:
            for handler in node.handlers:
                for i in pprint_inner (handler, level): yield i

        for i in pprint_orelse (node.orelse, level): yield i
        if len (node.finalbody)>0:
            yield '    '*level+'finally:\n'
            for i in pprint_body (node.finalbody, level+1): yield i

    elif t==Tuple:
        yield '( '
        for i in pprint_seq (node.elts): yield i
        yield ' )'

    elif t==UAdd:
        yield '+'

    elif t==USub:
        yield '-'

    elif t==UnaryOp:
        for i in pprint_inner (node.op): yield i
        for i in pprint_inner (node.operand): yield i

    elif t==While:
        yield 'while '
        for i in pprint_inner (node.test): yield i
        yield ':\n'
        for i in pprint_body (node.body, level+1): yield i
        for i in pprint_orelse (node.orelse, level): yield i

    elif t==With:
        yield 'with '
        for i in pprint_seq (node.items): yield i
        yield ':\n'
        for i in pprint_body (node.body, level+1): yield i

    elif t==Yield:
        # Yield(value=Attribute(value=Name(id='self', ctx=Load()), attr='left', ctx=Load()))
        yield 'yield '
        for i in pprint_inner (node.value): yield i

    elif t==YieldFrom:
        yield 'yield from '
        for i in pprint_inner (node.value): yield i

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

        for i in pprint_args (node.args, node.defaults): yield i

        if len (node.args)>0 and (node.vararg is not None or
                                  len (node.kwonlyargs)>0 or
                                  node.kwarg is not None):
            yield ', '

        if node.vararg is not None:
            yield '*'
            for i in pprint_inner (node.vararg): yield i

        if ((len (node.args)>0 or node.vararg is not None) and
            (len (node.kwonlyargs)>0 or node.kwarg is not None)):

            yield ', '

        for i in pprint_args (node.kwonlyargs, node.kw_defaults): yield i

        if ((len (node.args)>0 or
             node.vararg is not None or
             len (node.kwonlyargs)>0) and node.kwarg is not None):
            yield ', '

        if node.kwarg is not None:
            yield '**'
            for i in pprint_inner (node.kwarg): yield i

    elif t==comprehension:
        # comprehension(target=Name(id='i', ctx=Store()),
        #               iter=Attribute(value=Name(id='self', ctx=Load()),
        #                              attr='indexes', ctx=Load()),
        #               ifs=[Compare(left=..., ops=[IsNot()],
        #                            comparators=[NameConstant(value=None)])])
        # i in self.indexes if i.right is not None
        for i in pprint_inner (node.target): yield i
        yield ' in '
        for i in pprint_inner (node.iter): yield i

        if len (node.ifs)>0:
            # TODO: more
            yield ' if '
            for i in pprint_inner (node.ifs[0]): yield i

    elif t==keyword_type:
        # keyword(arg='end', value=Str(s=''))
        yield node.arg
        yield '='
        for i in pprint_inner (node.value): yield i

    elif t==withitem:
        # withitem(context_expr=..., optional_vars=Name(id='f', ctx=Store()))
        for i in pprint_inner (node.context_expr): yield i
        if node.optional_vars is not None:
            yield ' as '
            for i in pprint_inner (node.optional_vars): yield i

    else:
        yield '\n'
        yield '# unknown construction\n'
        yield dump (node)
