from ast import Module, ImportFrom, Expr, Call, Name, FunctionDef, Assign, Str
from ast import dump, If, Compare, Eq, For, Attribute, Gt, Num, IsNot, BinOp
from ast import NameConstant, Mult, Add, Import, List, Dict, Is, BoolOp, And
from ast import Subscript, Index, Tuple, Lt, Sub, Global, Return, AugAssign
from ast import While, UnaryOp, Not, ClassDef, Mod, Yield, NotEq, Try, Pass
from ast import ExceptHandler, Break, Slice, USub, ListComp, In, Lambda, BitAnd
from ast import BitOr, Or, Delete, Bytes, Raise, NotIn, RShift, GeneratorExp
from ast import Assert, Set, SetComp, LtE, IfExp, FloorDiv, GtE, With, Continue
from ast import YieldFrom, UAdd, LShift, DictComp, Div, Starred
from _ast import arguments, arg as arg_type, keyword as keyword_type
from _ast import alias as alias_type, comprehension, withitem

def pprint_body (body, level):
    for statement in body:
        print ('    '*level, end='')
        pprint (statement, level)
        print ()

def pprint_seq (seq, sep=', '):
    for i, e in enumerate (seq):
        if type (e)==str:
            print (e, end='')
        else:
            pprint (e)

        if i<len (seq)-1:
            if type (sep)==str:
                print (sep, end='')
            else:
                pprint (sep)

def pprint_orelse (orelse, level):
    if len (orelse)>0:
        print ('    '*level+'else:')
        pprint_body (orelse, level+1)

def pprint (node, level=0):
    # move down to the lineno
    # for lineno in range (line, node.lineno):
    #     print ()
    #     line+= 1
    t= type (node)

    if t==Module:
        # Module(body=[ ... ])
        pprint_body (node.body, 0)

    elif t==ImportFrom:
        # ImportFrom(module='ayrton.execute', names=[alias(name='Command', asname=None)], level=0)
        print ("from ", end='')
        print (node.module, end='')
        print (" import ", end='')
        pprint_seq (node.names)

    elif t==Import:
        # Import(names=[alias(name='ayrton', asname=None)])
        print ("import ", end='')
        pprint_seq (node.names)

    elif t==alias_type:
        print (node.name, end='')
        if node.asname is not None:
            print (" as ", end='')
            print (node.asname, end= '')

    elif t==Expr:
        # Expr(value=...)
        pprint (node.value, level)

    elif t==Call:
        # Call(func=Name(id='foo', ctx=Load()), args=[], keywords=[], starargs=None, kwargs=None)
        pprint (node.func)
        print (' (', end='')
        pprint_seq (node.args)
        if len (node.args)>0 and len (node.keywords)>0:
            print (', ', end='')
        pprint_seq (node.keywords)
        # TODO: more
        print (')', end='')

    elif t==Name:
        print (node.id, end='')

    elif t==FunctionDef:
        #FunctionDef(name='foo', args=arguments(...), body=[ ... ], decorator_list=[], returns=None)
        # TODO: decorator_list
        # TODO: returns
        print ('def ', node.name, ' (', end='')
        pprint (node.args, False)
        print ('):')
        pprint_body (node.body, level+1)

    elif t==arguments:
        # arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
        pprint_seq (node.args)
        # TODO: more

    elif t==Assign:
        # Assign(targets=[Name(id='c', ctx=Store())],
        #        value=...)
        pprint_seq (node.targets)
        print ('= ', end='')
        pprint (node.value)

    elif t==Str:
        # Str(s='true')
        print (repr (node.s), end='')

    elif t==arg_type:
        # arg(arg='node', annotation=None)
        print (node.arg, end='')

    elif t==If:
        # If(test=..., body=[...], orelse=[...]
        print ('if ', end='')
        pprint (node.test)
        print (':')
        pprint_body (node.body, level+1)

        if len (node.orelse)>0:
            # special case for elif
            if len (node.orelse)==1 and type (node.orelse[0])==If:
                print ('    '*level+'el', end='')
                pprint (node.orelse[0], level)
            else:
                pprint_orelse (node.orelse, level)

    elif t==Compare:
        # Compare(left=Name(id='t', ctx=Load()), ops=[Eq()], comparators=[Name(id='Module', ctx=Load())])
        # TODO: do properly
        pprint (node.left)
        for op in node.ops:
            pprint (op)

        for comparator in node.comparators:
            pprint (comparator)

    elif t==Eq:
        print ('==', end='')

    elif t==For:
        # For(target=..., iter=..., body=[...], orelse=[...]
        print ('for ', end='')
        pprint (node.target)
        print (' in ', end='')
        pprint (node.iter)
        print (':')
        pprint_body (node.body, level+1)
        pprint_orelse (node.orelse, level)

    elif t==Attribute:
        # Attribute(value=Name(id='node', ctx=Load()), attr='body', ctx=Load())
        pprint (node.value)
        print ('.', end='')
        print (node.attr, end='')

    elif t==Gt:
        print ('>', end='')

    elif t==Num:
        print (node.n, end='')

    elif t==keyword_type:
        # keyword(arg='end', value=Str(s=''))
        print (node.arg, end='')
        print ('=', end='')
        pprint (node.value)

    elif t==IsNot:
        print (' is not ', end='')

    elif t==NameConstant:
        print (node.value, end='')

    elif t==BinOp:
        pprint (node.left)
        pprint (node.op)
        pprint (node.right)

    elif t==Mult:
        print ('*', end='')

    elif t==Add:
        print ('+', end='')

    elif t==List:
        print ('[ ', end='')
        pprint_seq (node.elts)
        print (' ]', end='')

    elif t==Dict:
        print ('{ ', end='')
        for k, v in zip (node.keys, node.values):
            pprint (k)
            print ('=', end='')
            pprint (v)
            print (', ', end='')
        print (' }', end='')

    elif t==Is:
        print (' is ', end='')

    elif t==BoolOp:
        pprint_seq (node.values, node.op)

    elif t==And:
        print (' and ', end='')

    elif t==Subscript:
        # Subscript(value=Attribute(value=Name(id='node', ctx=Load()), attr='orelse', ctx=Load()),
        #           slice=Index(value=Num(n=0)), ctx=Load())
        pprint (node.value)
        print ('[', end='')
        pprint (node.slice)
        print (']', end='')

    elif t==Index:
        pprint (node.value)

    elif t==Tuple:
        print ('( ', end='')
        pprint_seq (node.elts)
        print (' )', end='')

    elif t==Lt:
        print ('<', end='')

    elif t==Sub:
        print ('-', end='')

    elif t==Global:
        print ('global ', end='')
        pprint_seq (node.names)

    elif t==Return:
        print ('return ', end='')
        if node.value is not None:
            pprint (node.value)

    elif t==AugAssign:
        # AugAssign(target=Name(id='ans', ctx=Store()), op=Add(), value=Name(id='a', ctx=Load()))
        pprint (node.target)
        pprint (node.op)
        print ('= ', end='')
        pprint (node.value)

    elif t==While:
        print ('while ', end='')
        pprint (node.test)
        print (':')
        pprint_body (node.body, level+1)
        pprint_orelse (node.orelse, level)

    elif t==UnaryOp:
        pprint (node.op)
        pprint (node.operand)

    elif t==Not:
        print ('not ', end='')

    elif t==ClassDef:
        # ClassDef(name='ToExpand', bases=[Name(id='object', ctx=Load())],
        #          keywords=[], starargs=None, kwargs=None, body=[...]
        print ('class ', end='')
        print (node.name, end='')

        # TODO: more
        if len (node.bases)>0:
            print (' (', end='')
            pprint_seq (node.bases)
            print (')', end='')

        print (':')
        pprint_body (node.body, level+1)

    elif t==Mod:
        print (' % ', end='')

    elif t==Yield:
        # Yield(value=Attribute(value=Name(id='self', ctx=Load()), attr='left', ctx=Load()))
        print ('yield ', end='')
        pprint (node.value)

    elif t==NotEq:
        print ('!=', end='')

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

    elif t==ExceptHandler:
        # ExceptHandler(type=Name(id='KeyError', ctx=Load()), name=None, body=[Pass()])
        print ('    '*level+'except ', end='')
        pprint (node.type)

        if node.name is not None:
            print (' as ', end='')
            print (node.name, end='')

        print (':')
        pprint_body (node.body, level+1)

    elif t==Pass:
        print ('pass')

    elif t==Break:
        print ('break')

    elif t==Slice:
        # Slice(lower=None, upper=Name(id='left_cb', ctx=Load()), step=None)
        if node.lower is not None:
            pprint (node.lower)

        print (':', end='')

        if node.upper is not None:
            pprint (node.upper)

        if node.step is not None:
            print (':', end='')
            pprint (node.step)

    elif t==USub:
        print ('-', end='')

    elif t==ListComp:
        # ListComp(elt=Name(id='i', ctx=Load()), generators=[...])
        # [ i for i in self.indexes if i.right is not None ]
        print ('[ ', end='')
        pprint (node.elt)
        print (' for ', end='')
        # TODO: more
        pprint (node.generators[0])
        print (' ]', end='')

    elif t==comprehension:
        # comprehension(target=Name(id='i', ctx=Store()),
        #               iter=Attribute(value=Name(id='self', ctx=Load()),
        #                              attr='indexes', ctx=Load()),
        #               ifs=[Compare(left=..., ops=[IsNot()],
        #                            comparators=[NameConstant(value=None)])])
        # i in self.indexes if i.right is not None
        pprint (node.target)
        print (' in ', end='')
        pprint (node.iter)

        if len (node.ifs)>0:
            # TODO: more
            print (' if ', end='')
            pprint (node.ifs[0])

    elif t==In:
        print (' in ', end='')

    elif t==Lambda:
        # Lambda(args=arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[]), body=Num(n=0))
        print ('lambda ', end='')
        pprint (node.args)
        print (': ', end='')
        pprint (node.body)

    elif t==BitAnd:
        print (' & ', end='')

    elif t==BitOr:
        print ('|', end='')

    elif t==Or:
        print (' or ', end='')

    elif t==Delete:
        print ('delete ', end='')
        pprint_seq (node.targets)

    elif t==Bytes:
        print (repr (node.s), end='')

    elif t==Raise:
        # Raise(exc=Call(func=Name(id='ValueError', ctx=Load()),
        #                args=[Str(s='too many lines')], keywords=[],
        #                starargs=None, kwargs=None),
        #       cause=None)
        print ('raise ', end='')
        pprint (node.exc)
        # TODO: cause?

    elif t==NotIn:
        print (' not in ', end='')

    elif t==RShift:
        print ('>>', end='')

    elif t==GeneratorExp:
        # GeneratorExp(elt=Name(id='line', ctx=Load()), generators=[...])
        print ('( ', end='')
        pprint (node.elt)
        print (' for ', end='')
        # TODO: more
        pprint (node.generators[0])
        print (' )', end='')

    elif t==Assert:
        # Assert(test=..., msg=None)
        print ('assert ', end='')
        pprint (node.test)
        # TODO: msg

    elif t==Set:
        print ('{ ', end='')
        pprint_seq (node.elts)
        print (' }', end='')

    elif t==SetComp:
        # SetComp(elt=Name(id='name', ctx=Load()), generators=[...])
        print ('{ ', end='')
        pprint (node.elt)
        print (' for ', end='')
        # TODO: more
        pprint (node.generators[0])

    elif t==LtE:
        print ('<=', end='')

    elif t==GtE:
        print ('>=', end='')

    elif t==IfExp:
        # IfExp(test=..., body=Str(s=''), orelse=Str(s='s'))
        pprint (node.body)
        print (' if ', end='')
        pprint (node.test)
        print (' else ', end='')
        pprint (node.orelse)

    elif t==FloorDiv:
        print ('\\\\', end='')

    elif t==With:
        print ('with ', end='')
        pprint_seq (node.items)
        print (':', end='')
        pprint_body (node.body, level+1)

    elif t==withitem:
        # withitem(context_expr=..., optional_vars=Name(id='f', ctx=Store()))
        pprint (node.context_expr)
        if node.optional_vars is not None:
            print (' as ', end='')
            pprint (node.optional_vars)

    elif t==Continue:
        print ('continue', end='')

    elif t==YieldFrom:
        print ('yield from ', end='')
        pprint (node.value)

    elif t==UAdd:
        print ('+', end='')

    elif t==LShift:
        print ('<<', end='')

    elif t==DictComp:
        # DictComp(key=Name(id='v', ctx=Load()), value=Name(id='k', ctx=Load()), generators=[comprehension(target=Tuple(elts=[Name(id='k', ctx=Store()), Name(id='v', ctx=Store())], ctx=Store()), iter=Call(func=Name(id='enumerate', ctx=Load()), args=[Name(id='_b32alphabet', ctx=Load())], keywords=[], starargs=None, kwargs=None), ifs=[])])
        print ('{ ', end='')
        pprint (node.key)
        print (': ', end='')
        pprint (node.value)
        print (' for ', end='')
        # TODO: more
        pprint (node.generators[0])
        print (' }', end='')

    elif t==Div:
        print ('/', end='')

    else:
        print ()
        print (dump (node))
