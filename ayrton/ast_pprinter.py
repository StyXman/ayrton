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

def atom (s):
    print (s, end='')

def pprint_body (body, level):
    for statement in body:
        atom ('    '*level)
        pprint (statement, level)
        print ()

def pprint_seq (seq, sep=', '):
    for i, e in enumerate (seq):
        if type (e)==str:
            atom (e)
        else:
            pprint (e)

        if i<len (seq)-1:
            if type (sep)==str:
                atom (sep)
            else:
                pprint (sep)

def pprint_orelse (orelse, level):
    if len (orelse)>0:
        print ('    '*level+'else:')
        pprint_body (orelse, level+1)

def pprint_args (args, defaults):
    # TODO: anotations
    # args=[arg(arg='a', annotation=None), arg(arg='b', annotation=None)]
    # defaults=[Num(n=1)]
    d_index= len (args)-len (defaults)
    for index, arg in enumerate (args):
        atom (arg.arg)

        if index>=d_index:
            atom ('=')
            pprint (defaults[index-d_index])

        if index<len (args)-1:
            atom (', ')

def pprint (node, level=0):
    # move down to the lineno
    # for lineno in range (line, node.lineno):
    #     print ()
    #     line+= 1
    t= type (node)

    if t==Add:
        atom ('+')

    elif t==And:
        atom (' and ')

    elif t==Assert:
        # Assert(test=..., msg=None)
        atom ('assert ')
        pprint (node.test)
        # TODO: msg

    elif t==Assign:
        # Assign(targets=[Name(id='c', ctx=Store())],
        #        value=...)
        pprint_seq (node.targets)
        atom ('= ')
        pprint (node.value)

    elif t==Attribute:
        # Attribute(value=Name(id='node', ctx=Load()), attr='body', ctx=Load())
        pprint (node.value)
        atom ('.')
        atom (node.attr)

    elif t==AugAssign:
        # AugAssign(target=Name(id='ans', ctx=Store()), op=Add(), value=Name(id='a', ctx=Load()))
        pprint (node.target)
        pprint (node.op)
        atom ('= ')
        pprint (node.value)

    elif t==BinOp:
        # BUG:
        # m= ast.parse ('5*(3+4)')
        # ayrton.ast_pprinter.pprint (m)
        # 5*3+4
        pprint (node.left)
        pprint (node.op)
        pprint (node.right)

    elif t==BitAnd:
        atom (' & ')

    elif t==BitOr:
        atom ('|')

    elif t==BitXor:
        atom ('^')

    elif t==BoolOp:
        pprint_seq (node.values, node.op)

    elif t==Break:
        print ('break')

    elif t==Bytes:
        atom (repr (node.s))

    elif t==Call:
        # Call(func=Name(id='foo', ctx=Load()), args=[], keywords=[], starargs=None, kwargs=None)
        # TODO: annotations
        pprint (node.func)
        atom (' (')
        pprint_seq (node.args)

        if len (node.args)>0 and (len (node.keywords)>0 or
                                  node.starargs is not None or
                                  node.kwargs is not None):
            atom (', ')

        pprint_seq (node.keywords)

        if ((len (node.args)>0 or len (node.keywords)>0) and
            (node.starargs is not None or node.kwargs is not None)):
            atom (', ')

        if node.starargs is not None:
            atom ('*')
            pprint (node.starargs)

        if ((len (node.args)>0 or
             len (node.keywords)>0 or
             (node.starargs is not None) and node.kwargs is not None)):
            atom (', ')

        if node.kwargs is not None:
            atom ('**')
            pprint (node.kwargs)

        atom (')')

    elif t==ClassDef:
        # ClassDef(name='ToExpand', bases=[Name(id='object', ctx=Load())],
        #          keywords=[], starargs=None, kwargs=None, body=[...]
        atom ('class ')
        atom (node.name)

        # TODO: more
        if len (node.bases)>0:
            atom (' (')
            pprint_seq (node.bases)
            atom (')')

        print (':')
        pprint_body (node.body, level+1)

    elif t==Compare:
        # Compare(left=Name(id='t', ctx=Load()), ops=[Eq()], comparators=[Name(id='Module', ctx=Load())])
        # TODO: do properly
        pprint (node.left)
        for op in node.ops:
            pprint (op)

        for comparator in node.comparators:
            pprint (comparator)

    elif t==Continue:
        atom ('continue')

    elif t==Delete:
        atom ('delete ')
        pprint_seq (node.targets)

    elif t==Dict:
        atom ('{ ')
        for k, v in zip (node.keys, node.values):
            pprint (k)
            atom ('=')
            pprint (v)
            atom (', ')
        atom (' }')

    elif t==DictComp:
        # DictComp(key=Name(id='v', ctx=Load()), value=Name(id='k', ctx=Load()), generators=[comprehension(target=Tuple(elts=[Name(id='k', ctx=Store()), Name(id='v', ctx=Store())], ctx=Store()), iter=Call(func=Name(id='enumerate', ctx=Load()), args=[Name(id='_b32alphabet', ctx=Load())], keywords=[], starargs=None, kwargs=None), ifs=[])])
        atom ('{ ')
        pprint (node.key)
        atom (': ')
        pprint (node.value)
        atom (' for ')
        # TODO: more
        pprint (node.generators[0])
        atom (' }')

    elif t==Div:
        atom ('/')

    elif t==Eq:
        atom ('==')

    elif t==ExceptHandler:
        # ExceptHandler(type=Name(id='KeyError', ctx=Load()), name=None, body=[Pass()])
        atom ('    '*level+'except ')
        if node.type is not None:
            pprint (node.type)
            if node.name is not None:
                atom (' as ')
                atom (node.name)

        print (':')
        pprint_body (node.body, level+1)

    elif t==Expr:
        # Expr(value=...)
        pprint (node.value, level)

    elif t==FloorDiv:
        atom ('\\\\')

    elif t==For:
        # For(target=..., iter=..., body=[...], orelse=[...]
        atom ('for ')
        pprint (node.target)
        atom (' in ')
        pprint (node.iter)
        print (':')
        pprint_body (node.body, level+1)
        pprint_orelse (node.orelse, level)

    elif t==FunctionDef:
        #FunctionDef(name='foo', args=arguments(...), body=[ ... ], decorator_list=[], returns=None)
        # TODO: decorator_list
        # TODO: returns
        atom ('def ', node.name, ' (')
        pprint (node.args)
        print ('):')
        pprint_body (node.body, level+1)

    elif t==GeneratorExp:
        # GeneratorExp(elt=Name(id='line', ctx=Load()), generators=[...])
        atom ('( ')
        pprint (node.elt)
        atom (' for ')
        # TODO: more
        pprint (node.generators[0])
        atom (' )')

    elif t==Global:
        atom ('global ')
        pprint_seq (node.names)

    elif t==Gt:
        atom ('>')

    elif t==GtE:
        atom ('>=')

    elif t==If:
        # If(test=..., body=[...], orelse=[...]
        atom ('if ')
        pprint (node.test)
        print (':')
        pprint_body (node.body, level+1)

        if len (node.orelse)>0:
            # special case for elif
            if len (node.orelse)==1 and type (node.orelse[0])==If:
                atom ('    '*level+'el')
                pprint (node.orelse[0], level)
            else:
                pprint_orelse (node.orelse, level)

    elif t==IfExp:
        # IfExp(test=..., body=Str(s=''), orelse=Str(s='s'))
        pprint (node.body)
        atom (' if ')
        pprint (node.test)
        atom (' else ')
        pprint (node.orelse)

    elif t==Import:
        # Import(names=[alias(name='ayrton', asname=None)])
        atom ("import ")
        pprint_seq (node.names)

    elif t==ImportFrom:
        # ImportFrom(module='ayrton.execute', names=[alias(name='Command', asname=None)], level=0)
        atom ("from ")
        atom (node.module)
        atom (" import ")
        pprint_seq (node.names)

    elif t==In:
        atom (' in ')

    elif t==Index:
        pprint (node.value)

    elif t==Is:
        atom (' is ')

    elif t==IsNot:
        atom (' is not ')

    elif t==LShift:
        atom ('<<')

    elif t==Lambda:
        # Lambda(args=arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=Num(n=0))
        atom ('lambda ')
        pprint (node.args)
        atom (': ')
        pprint (node.body)

    elif t==List:
        atom ('[ ')
        pprint_seq (node.elts)
        atom (' ]')

    elif t==ListComp:
        # ListComp(elt=Name(id='i', ctx=Load()), generators=[...])
        # [ i for i in self.indexes if i.right is not None ]
        atom ('[ ')
        pprint (node.elt)
        atom (' for ')
        # TODO: more
        pprint (node.generators[0])
        atom (' ]')

    elif t==Lt:
        atom ('<')

    elif t==LtE:
        atom ('<=')

    elif t==Mod:
        atom (' % ')

    elif t==Module:
        # Module(body=[ ... ])
        pprint_body (node.body, 0)

    elif t==Mult:
        atom ('*')

    elif t==Name:
        atom (node.id)

    elif t==NameConstant:
        atom (node.value)

    elif t==Not:
        atom ('not ')

    elif t==NotEq:
        atom ('!=')

    elif t==NotIn:
        atom (' not in ')

    elif t==Num:
        atom (node.n)

    elif t==Or:
        atom (' or ')

    elif t==Pass:
        print ('pass')

    elif t==Pow:
        atom ('**')

    elif t==RShift:
        atom ('>>')

    elif t==Raise:
        # Raise(exc=Call(func=Name(id='ValueError', ctx=Load()),
        #                args=[Str(s='too many lines')], keywords=[],
        #                starargs=None, kwargs=None),
        #       cause=None)
        atom ('raise ')
        if node.exc is not None:
            pprint (node.exc)
        # TODO: cause?

    elif t==Return:
        atom ('return ')
        if node.value is not None:
            pprint (node.value)

    elif t==Set:
        atom ('{ ')
        pprint_seq (node.elts)
        atom (' }')

    elif t==SetComp:
        # SetComp(elt=Name(id='name', ctx=Load()), generators=[...])
        atom ('{ ')
        pprint (node.elt)
        atom (' for ')
        # TODO: more
        pprint (node.generators[0])

    elif t==Slice:
        # Slice(lower=None, upper=Name(id='left_cb', ctx=Load()), step=None)
        if node.lower is not None:
            pprint (node.lower)

        atom (':')

        if node.upper is not None:
            pprint (node.upper)

        if node.step is not None:
            atom (':')
            pprint (node.step)

    elif t==Str:
        # Str(s='true')
        atom (repr (node.s))

    elif t==Sub:
        atom ('-')

    elif t==Subscript:
        # Subscript(value=Attribute(value=Name(id='node', ctx=Load()), attr='orelse', ctx=Load()),
        #           slice=Index(value=Num(n=0)), ctx=Load())
        pprint (node.value)
        atom ('[')
        pprint (node.slice)
        atom (']')

    elif t==Try:
        # Try(body=[...],  handlers=[...], orelse=[], finalbody=[])
        print ('try:')
        pprint_body (node.body, level+1)
        if len (node.handlers)>0:
            for handler in node.handlers:
                pprint (handler, level)

        pprint_orelse (node.orelse, level)
        if len (node.finalbody)>0:
            print ('    '*level+'finally:')
            pprint_body (node.finalbody, level+1)

    elif t==Tuple:
        atom ('( ')
        pprint_seq (node.elts)
        atom (' )')

    elif t==UAdd:
        atom ('+')

    elif t==USub:
        atom ('-')

    elif t==UnaryOp:
        pprint (node.op)
        pprint (node.operand)

    elif t==While:
        atom ('while ')
        pprint (node.test)
        print (':')
        pprint_body (node.body, level+1)
        pprint_orelse (node.orelse, level)

    elif t==With:
        atom ('with ')
        pprint_seq (node.items)
        atom (':')
        pprint_body (node.body, level+1)

    elif t==Yield:
        # Yield(value=Attribute(value=Name(id='self', ctx=Load()), attr='left', ctx=Load()))
        atom ('yield ')
        pprint (node.value)

    elif t==YieldFrom:
        atom ('yield from ')
        pprint (node.value)

    elif t==alias_type:
        atom (node.name)
        if node.asname is not None:
            atom (" as ")
            print (node.asname, end= '')

    elif t==arg_type:
        # arg(arg='node', annotation=None)
        # TODO: annotation
        atom (node.arg)

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

        pprint_args (node.args, node.defaults)

        if len (node.args)>0 and (node.vararg is not None or
                                  len (node.kwonlyargs)>0 or
                                  node.kwarg is not None):
            atom (', ')

        if node.vararg is not None:
            atom ('*')
            pprint (node.vararg)

        if ((len (node.args)>0 or node.vararg is not None) and
            (len (node.kwonlyargs)>0 or node.kwarg is not None)):

            atom (', ')

        pprint_args (node.kwonlyargs, node.kw_defaults)

        if ((len (node.args)>0 or
             node.vararg is not None or
             len (node.kwonlyargs)>0) and node.kwarg is not None):
            atom (', ')

        if node.kwarg is not None:
            atom ('**')
            pprint (node.kwarg)

    elif t==comprehension:
        # comprehension(target=Name(id='i', ctx=Store()),
        #               iter=Attribute(value=Name(id='self', ctx=Load()),
        #                              attr='indexes', ctx=Load()),
        #               ifs=[Compare(left=..., ops=[IsNot()],
        #                            comparators=[NameConstant(value=None)])])
        # i in self.indexes if i.right is not None
        pprint (node.target)
        atom (' in ')
        pprint (node.iter)

        if len (node.ifs)>0:
            # TODO: more
            atom (' if ')
            pprint (node.ifs[0])

    elif t==keyword_type:
        # keyword(arg='end', value=Str(s=''))
        atom (node.arg)
        atom ('=')
        pprint (node.value)

    elif t==withitem:
        # withitem(context_expr=..., optional_vars=Name(id='f', ctx=Store()))
        pprint (node.context_expr)
        if node.optional_vars is not None:
            atom (' as ')
            pprint (node.optional_vars)

    else:
        print ()
        print (dump (node))
