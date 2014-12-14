from ast import Module, ImportFrom, Expr, Call, Name, FunctionDef, Assign, Str
from _ast import arguments

def pprint (node, indent=True, level=0):
    # move down to the lineno
    # for lineno in range (line, node.lineno):
    #     print ()
    #     line+= 1
    t= type (node)

    if t==Module:
        # Module(body=[ ... ])
        for statement in node.body:
            print ('    '*level, end='')
            pprint (statement, indent, level)
            print ()

    elif t==ImportFrom:
        # ImportFrom(module='ayrton.execute', names=[alias(name='Command', asname=None)], level=0)
        # TODO: level?
        if len (node.names)>0:
            # from foo import bar
            print ("from ", node.module, " import ", end='')
            for alias in node.names:
                print (alias.name, end='')
                if alias.asname is not None:
                    print (" as ", alias.asname, ", ", end= '')
        else:
            # import foo
            print ("import ", node.module, end='')

    elif t==Expr:
        # Expr(value=...)
        pprint (node.value, indent, level)

    elif t==Call:
        # Call(func=Name(id='foo', ctx=Load()), args=[], keywords=[], starargs=None, kwargs=None)
        pprint (node.func)
        print (' (', end='')

        for arg in node.args:
            pprint (arg, False)
        for keyword in node.keywords:
            pprint (keyword, False)

        print (')', end='')

    elif t==Name:
        print (node.id, end='')

    elif t==FunctionDef:
        #FunctionDef(name='foo', args=arguments(...), body=[ ... ], decorator_list=[], returns=None)
        # TODO: decorator_list
        # TODO: returns
        level+= 1
        print ('def ', node.name, ' (', end='')
        pprint (node.args, False)
        print ('):')
        for statement in node.body:
            print ('    '*level, end='')
            pprint (statement)
            print ()

    elif t==arguments:
        # arguments(args=[], vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None, defaults=[])
        for arg in node.args:
            pprint (arg)
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

    else:
        print (node)
