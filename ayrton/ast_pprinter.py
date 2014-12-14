from ast import Module, ImportFrom, Expr, Call, Name, FunctionDef, Assign, Str
from ast import dump, If, Compare, Eq, For, Attribute, Gt, Num, IsNot, BinOp
from ast import NameConstant, Mult, Add
from _ast import arguments, arg as arg_type, keyword as keyword_type

def pprint (node, level=0):
    # move down to the lineno
    # for lineno in range (line, node.lineno):
    #     print ()
    #     line+= 1
    t= type (node)

    if t==Module:
        # Module(body=[ ... ])
        for statement in node.body:
            pprint (statement, level)
            print ()

    elif t==ImportFrom:
        # ImportFrom(module='ayrton.execute', names=[alias(name='Command', asname=None)], level=0)
        # TODO: level?
        if len (node.names)>0:
            # from foo import bar
            print ("from ", end='')
            print (node.module, end='')
            print (" import ", end='')
            for alias in node.names:
                print (alias.name, end='')
                if alias.asname is not None:
                    print (" as ", end='')
                    print (alias.asname, end= '')
                print (', ', end='')
        else:
            # import foo
            print ("import ", node.module, end='')

    elif t==Expr:
        # Expr(value=...)
        pprint (node.value, level)

    elif t==Call:
        # Call(func=Name(id='foo', ctx=Load()), args=[], keywords=[], starargs=None, kwargs=None)
        pprint (node.func)
        print (' (', end='')

        for arg in node.args:
            pprint (arg, False)
            print (', ', end='')
        for keyword in node.keywords:
            pprint (keyword, False)
            print (', ', end='')

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
        for statement in node.body:
            print ('    '*(level+1), end='')
            pprint (statement, level+1)
            print ()

    elif t==arguments:
        # arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
        for arg in node.args:
            pprint (arg)
            print (', ', end='')
        # TODO: more

    elif t==Assign:
        # Assign(targets=[Name(id='c', ctx=Store())],
        #        value=...)
        for target in node.targets:
            pprint (target)
            print (', ', end='')

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
        for statement in node.body:
            print ('    '*(level+1), end='')
            pprint (statement, level+1)
            print ()

        if len (node.orelse)>0:
            # special case for elif
            # if len (node.orelse)==1 and type (node.orelse[0])==If:
            #     print ('    '*level+'elif ', end='')
                # TODO
            # else:
            print ('    '*level+'else:')
            for statement in node.orelse:
                print ('    '*(level+1), end='')
                pprint (statement, level+1)
                print ()

    elif t==Compare:
        # Compare(left=Name(id='t', ctx=Load()), ops=[Eq()], comparators=[Name(id='Module', ctx=Load())])
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

        for statement in node.body:
            print ('    '*(level+1), end='')
            pprint (statement, level+1)
            print ()

        if len (node.orelse)>0:
            print ('    '*level+'else:')
            for statement in node.orelse:
                print ('    '*(level+1), end='')
                pprint (statement, level+1)
                print ()

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

    else:
        print ()
        print (dump (node))
