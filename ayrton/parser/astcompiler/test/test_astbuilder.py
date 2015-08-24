# -*- coding: utf-8 -*-
import random
import string
import sys
import py
from pypy.interpreter.baseobjspace import W_Root
from pypy.interpreter.pyparser import pyparse
from pypy.interpreter.pyparser.error import SyntaxError
from pypy.interpreter.astcompiler.astbuilder import ast_from_node
from pypy.interpreter.astcompiler import ast, consts


class TestAstBuilder:

    def setup_class(cls):
        cls.parser = pyparse.PythonParser(cls.space)

    def get_ast(self, source, p_mode=None, flags=None):
        if p_mode is None:
            p_mode = "exec"
        if flags is None:
            flags = consts.CO_FUTURE_WITH_STATEMENT
        info = pyparse.CompileInfo("<test>", p_mode, flags)
        tree = self.parser.parse_source(source, info)
        ast_node = ast_from_node(self.space, tree, info)
        return ast_node

    def get_first_expr(self, source, p_mode=None, flags=None):
        mod = self.get_ast(source, p_mode, flags)
        assert len(mod.body) == 1
        expr = mod.body[0]
        assert isinstance(expr, ast.Expr)
        return expr.value

    def get_first_stmt(self, source):
        mod = self.get_ast(source)
        assert len(mod.body) == 1
        return mod.body[0]

    def test_top_level(self):
        mod = self.get_ast("hi = 32")
        assert isinstance(mod, ast.Module)
        body = mod.body
        assert len(body) == 1

        mod = self.get_ast("hi", p_mode="eval")
        assert isinstance(mod, ast.Expression)
        assert isinstance(mod.body, ast.expr)

        mod = self.get_ast("x = 23", p_mode="single")
        assert isinstance(mod, ast.Interactive)
        assert len(mod.body) == 1
        mod = self.get_ast("x = 23; y = 23; b = 23", p_mode="single")
        assert isinstance(mod, ast.Interactive)
        assert len(mod.body) == 3
        for stmt in mod.body:
            assert isinstance(stmt, ast.Assign)
        assert mod.body[-1].targets[0].id == "b"

        mod = self.get_ast("x = 23; y = 23; b = 23")
        assert isinstance(mod, ast.Module)
        assert len(mod.body) == 3
        for stmt in mod.body:
            assert isinstance(stmt, ast.Assign)

    def test_del(self):
        d = self.get_first_stmt("del x")
        assert isinstance(d, ast.Delete)
        assert len(d.targets) == 1
        assert isinstance(d.targets[0], ast.Name)
        assert d.targets[0].ctx == ast.Del
        d = self.get_first_stmt("del x, y")
        assert len(d.targets) == 2
        assert d.targets[0].ctx == ast.Del
        assert d.targets[1].ctx == ast.Del
        d = self.get_first_stmt("del x.y")
        assert len(d.targets) == 1
        attr = d.targets[0]
        assert isinstance(attr, ast.Attribute)
        assert attr.ctx == ast.Del
        d = self.get_first_stmt("del x[:]")
        assert len(d.targets) == 1
        sub = d.targets[0]
        assert isinstance(sub, ast.Subscript)
        assert sub.ctx == ast.Del

    def test_break(self):
        br = self.get_first_stmt("while True: break").body[0]
        assert isinstance(br, ast.Break)

    def test_continue(self):
        cont = self.get_first_stmt("while True: continue").body[0]
        assert isinstance(cont, ast.Continue)

    def test_return(self):
        ret = self.get_first_stmt("def f(): return").body[0]
        assert isinstance(ret, ast.Return)
        assert ret.value is None
        ret = self.get_first_stmt("def f(): return x").body[0]
        assert isinstance(ret.value, ast.Name)

    def test_raise(self):
        ra = self.get_first_stmt("raise")
        assert ra.exc is None
        assert ra.cause is None
        ra = self.get_first_stmt("raise x")
        assert isinstance(ra.exc, ast.Name)
        assert ra.cause is None
        ra = self.get_first_stmt("raise x from 3")
        assert isinstance(ra.exc, ast.Name)
        assert isinstance(ra.cause, ast.Num)

    def test_import(self):
        im = self.get_first_stmt("import x")
        assert isinstance(im, ast.Import)
        assert len(im.names) == 1
        alias = im.names[0]
        assert isinstance(alias, ast.alias)
        assert alias.name == "x"
        assert alias.asname is None
        im = self.get_first_stmt("import x.y")
        assert len(im.names) == 1
        alias = im.names[0]
        assert alias.name == "x.y"
        assert alias.asname is None
        im = self.get_first_stmt("import x as y")
        assert len(im.names) == 1
        alias = im.names[0]
        assert alias.name == "x"
        assert alias.asname == "y"
        im = self.get_first_stmt("import x, y as w")
        assert len(im.names) == 2
        a1, a2 = im.names
        assert a1.name == "x"
        assert a1.asname is None
        assert a2.name == "y"
        assert a2.asname == "w"
        exc = py.test.raises(SyntaxError, self.get_ast, "import x a b").value

    def test_from_import(self):
        im = self.get_first_stmt("from x import y")
        assert isinstance(im, ast.ImportFrom)
        assert im.module == "x"
        assert im.level == 0
        assert len(im.names) == 1
        a = im.names[0]
        assert isinstance(a, ast.alias)
        assert a.name == "y"
        assert a.asname is None
        im = self.get_first_stmt("from . import y")
        assert im.level == 1
        assert im.module is None
        im = self.get_first_stmt("from ... import y")
        assert im.level == 3
        assert im.module is None
        im = self.get_first_stmt("from .x import y")
        assert im.level == 1
        assert im.module == "x"
        im = self.get_first_stmt("from ..x.y import m")
        assert im.level == 2
        assert im.module == "x.y"
        im = self.get_first_stmt("from x import *")
        assert len(im.names) == 1
        a = im.names[0]
        assert a.name == "*"
        assert a.asname is None
        for input in ("from x import x, y", "from x import (x, y)"):
            im = self.get_first_stmt(input)
            assert len(im.names) == 2
            a1, a2 = im.names
            assert a1.name == "x"
            assert a1.asname is None
            assert a2.name == "y"
            assert a2.asname is None
        for input in ("from x import a as b, w", "from x import (a as b, w)"):
            im = self.get_first_stmt(input)
            assert len(im.names) == 2
            a1, a2 = im.names
            assert a1.name == "a"
            assert a1.asname == "b"
            assert a2.name == "w"
            assert a2.asname is None
        input = "from x import y a b"
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        input = "from x import a, b,"
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        assert exc.msg == "trailing comma is only allowed with surronding " \
            "parenthesis"

    def test_global(self):
        glob = self.get_first_stmt("global x")
        assert isinstance(glob, ast.Global)
        assert glob.names == ["x"]
        glob = self.get_first_stmt("global x, y")
        assert glob.names == ["x", "y"]

    def test_nonlocal(self):
        nonloc = self.get_first_stmt("nonlocal x")
        assert isinstance(nonloc, ast.Nonlocal)
        assert nonloc.names == ["x"]
        nonloc = self.get_first_stmt("nonlocal x, y")
        assert nonloc.names == ["x", "y"]

    def test_assert(self):
        asrt = self.get_first_stmt("assert x")
        assert isinstance(asrt, ast.Assert)
        assert isinstance(asrt.test, ast.Name)
        assert asrt.msg is None
        asrt = self.get_first_stmt("assert x, 'hi'")
        assert isinstance(asrt.test, ast.Name)
        assert isinstance(asrt.msg, ast.Str)

    def test_suite(self):
        suite = self.get_first_stmt("while x: n;").body
        assert len(suite) == 1
        assert isinstance(suite[0].value, ast.Name)
        suite = self.get_first_stmt("while x: n").body
        assert len(suite) == 1
        suite = self.get_first_stmt("while x: \n    n;").body
        assert len(suite) == 1
        suite = self.get_first_stmt("while x: n;").body
        assert len(suite) == 1
        suite = self.get_first_stmt("while x:\n    n; f;").body
        assert len(suite) == 2

    def test_if(self):
        if_ = self.get_first_stmt("if x: 4")
        assert isinstance(if_, ast.If)
        assert isinstance(if_.test, ast.Name)
        assert if_.test.ctx == ast.Load
        assert len(if_.body) == 1
        assert isinstance(if_.body[0].value, ast.Num)
        assert if_.orelse is None
        if_ = self.get_first_stmt("if x: 4\nelse: 'hi'")
        assert isinstance(if_.test, ast.Name)
        assert len(if_.body) == 1
        assert isinstance(if_.body[0].value, ast.Num)
        assert len(if_.orelse) == 1
        assert isinstance(if_.orelse[0].value, ast.Str)
        if_ = self.get_first_stmt("if x: 3\nelif 'hi': pass")
        assert isinstance(if_.test, ast.Name)
        assert len(if_.orelse) == 1
        sub_if = if_.orelse[0]
        assert isinstance(sub_if, ast.If)
        assert isinstance(sub_if.test, ast.Str)
        assert sub_if.orelse is None
        if_ = self.get_first_stmt("if x: pass\nelif 'hi': 3\nelse: ()")
        assert isinstance(if_.test, ast.Name)
        assert len(if_.body) == 1
        assert isinstance(if_.body[0], ast.Pass)
        assert len(if_.orelse) == 1
        sub_if = if_.orelse[0]
        assert isinstance(sub_if, ast.If)
        assert isinstance(sub_if.test, ast.Str)
        assert len(sub_if.body) == 1
        assert isinstance(sub_if.body[0].value, ast.Num)
        assert len(sub_if.orelse) == 1
        assert isinstance(sub_if.orelse[0].value, ast.Tuple)

    def test_while(self):
        wh = self.get_first_stmt("while x: pass")
        assert isinstance(wh, ast.While)
        assert isinstance(wh.test, ast.Name)
        assert wh.test.ctx == ast.Load
        assert len(wh.body) == 1
        assert isinstance(wh.body[0], ast.Pass)
        assert wh.orelse is None
        wh = self.get_first_stmt("while x: pass\nelse: 4")
        assert isinstance(wh.test, ast.Name)
        assert len(wh.body) == 1
        assert isinstance(wh.body[0], ast.Pass)
        assert len(wh.orelse) == 1
        assert isinstance(wh.orelse[0].value, ast.Num)

    def test_for(self):
        fr = self.get_first_stmt("for x in y: pass")
        assert isinstance(fr, ast.For)
        assert isinstance(fr.target, ast.Name)
        assert fr.target.ctx == ast.Store
        assert isinstance(fr.iter, ast.Name)
        assert fr.iter.ctx == ast.Load
        assert len(fr.body) == 1
        assert isinstance(fr.body[0], ast.Pass)
        assert fr.orelse is None
        fr = self.get_first_stmt("for x, in y: pass")
        tup = fr.target
        assert isinstance(tup, ast.Tuple)
        assert tup.ctx == ast.Store
        assert len(tup.elts) == 1
        assert isinstance(tup.elts[0], ast.Name)
        assert tup.elts[0].ctx == ast.Store
        fr = self.get_first_stmt("for x, y in g: pass")
        tup = fr.target
        assert isinstance(tup, ast.Tuple)
        assert tup.ctx == ast.Store
        assert len(tup.elts) == 2
        for elt in tup.elts:
            assert isinstance(elt, ast.Name)
            assert elt.ctx == ast.Store
        fr = self.get_first_stmt("for x in g: pass\nelse: 4")
        assert len(fr.body) == 1
        assert isinstance(fr.body[0], ast.Pass)
        assert len(fr.orelse) == 1
        assert isinstance(fr.orelse[0].value, ast.Num)

    def test_try(self):
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "finally: pass")
        assert isinstance(tr, ast.Try)
        assert len(tr.body) == 1
        assert isinstance(tr.body[0].value, ast.Name)
        assert len(tr.finalbody) == 1
        assert isinstance(tr.finalbody[0], ast.Pass)
        assert tr.orelse is None
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except: pass")
        assert isinstance(tr, ast.Try)
        assert len(tr.body) == 1
        assert isinstance(tr.body[0].value, ast.Name)
        assert len(tr.handlers) == 1
        handler = tr.handlers[0]
        assert isinstance(handler, ast.excepthandler)
        assert handler.type is None
        assert handler.name is None
        assert len(handler.body) == 1
        assert isinstance(handler.body[0], ast.Pass)
        assert tr.orelse is None
        assert tr.finalbody is None
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except Exception: pass")
        assert len(tr.handlers) == 1
        handler = tr.handlers[0]
        assert isinstance(handler.type, ast.Name)
        assert handler.type.ctx == ast.Load
        assert handler.name is None
        assert len(handler.body) == 1
        assert tr.orelse is None
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except Exception as e: pass")
        assert len(tr.handlers) == 1
        handler = tr.handlers[0]
        assert isinstance(handler.type, ast.Name)
        assert handler.type.id == "Exception"
        assert handler.name == "e"
        assert len(handler.body) == 1
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except: pass" + "\n" +
                                 "else: 4")
        assert len(tr.body) == 1
        assert isinstance(tr.body[0].value, ast.Name)
        assert len(tr.handlers) == 1
        assert isinstance(tr.handlers[0].body[0], ast.Pass)
        assert len(tr.orelse) == 1
        assert isinstance(tr.orelse[0].value, ast.Num)
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except Exc as a: 5" + "\n" +
                                 "except F: pass")
        assert len(tr.handlers) == 2
        h1, h2 = tr.handlers
        assert isinstance(h1.type, ast.Name)
        assert h1.name == "a"
        assert isinstance(h1.body[0].value, ast.Num)
        assert isinstance(h2.type, ast.Name)
        assert h2.name is None
        assert isinstance(h2.body[0], ast.Pass)
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except Exc as a: 5" + "\n" +
                                 "except F: pass")
        assert len(tr.handlers) == 2
        h1, h2 = tr.handlers
        assert isinstance(h1.type, ast.Name)
        assert h1.name == "a"
        assert isinstance(h1.body[0].value, ast.Num)
        assert isinstance(h2.type, ast.Name)
        assert h2.name is None
        assert isinstance(h2.body[0], ast.Pass)
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except: 4" + "\n" +
                                 "finally: pass")
        assert isinstance(tr, ast.Try)
        assert len(tr.finalbody) == 1
        assert isinstance(tr.finalbody[0], ast.Pass)
        assert len(tr.handlers) == 1
        assert len(tr.handlers[0].body) == 1
        assert isinstance(tr.handlers[0].body[0].value, ast.Num)
        assert len(tr.body) == 1
        assert isinstance(tr.body[0].value, ast.Name)
        tr = self.get_first_stmt("try: x" + "\n" +
                                 "except: 4" + "\n" +
                                 "else: 'hi'" + "\n" +
                                 "finally: pass")
        assert isinstance(tr, ast.Try)
        assert len(tr.finalbody) == 1
        assert isinstance(tr.finalbody[0], ast.Pass)
        assert len(tr.body) == 1
        assert len(tr.orelse) == 1
        assert isinstance(tr.orelse[0].value, ast.Str)
        assert len(tr.body) == 1
        assert isinstance(tr.body[0].value, ast.Name)
        assert len(tr.handlers) == 1

    def test_with(self):
        wi = self.get_first_stmt("with x: pass")
        assert isinstance(wi, ast.With)
        assert len(wi.items) == 1
        assert isinstance(wi.items[0], ast.withitem)
        assert isinstance(wi.items[0].context_expr, ast.Name)
        assert wi.items[0].optional_vars is None
        assert len(wi.body) == 1
        wi = self.get_first_stmt("with x as y: pass")
        assert isinstance(wi.items[0].context_expr, ast.Name)
        assert len(wi.body) == 1
        assert isinstance(wi.items[0].optional_vars, ast.Name)
        assert wi.items[0].optional_vars.ctx == ast.Store
        wi = self.get_first_stmt("with x as (y,): pass")
        assert isinstance(wi.items[0].optional_vars, ast.Tuple)
        assert len(wi.items[0].optional_vars.elts) == 1
        assert wi.items[0].optional_vars.ctx == ast.Store
        assert wi.items[0].optional_vars.elts[0].ctx == ast.Store
        input = "with x hi y: pass"
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        wi = self.get_first_stmt("with x as y, b: pass")
        assert isinstance(wi, ast.With)
        assert len(wi.items) == 2
        assert isinstance(wi.items[0].context_expr, ast.Name)
        assert wi.items[0].context_expr.id == "x"
        assert isinstance(wi.items[0].optional_vars, ast.Name)
        assert wi.items[0].optional_vars.id == "y"
        assert isinstance(wi.items[1].context_expr, ast.Name)
        assert wi.items[1].context_expr.id == "b"
        assert wi.items[1].optional_vars is None
        assert len(wi.body) == 1
        assert isinstance(wi.body[0], ast.Pass)

    def test_class(self):
        for input in ("class X: pass", "class X(): pass"):
            cls = self.get_first_stmt(input)
            assert isinstance(cls, ast.ClassDef)
            assert cls.name == "X"
            assert len(cls.body) == 1
            assert isinstance(cls.body[0], ast.Pass)
            assert cls.bases is None
            assert cls.decorator_list is None
        for input in ("class X(Y): pass", "class X(Y,): pass"):
            cls = self.get_first_stmt(input)
            assert len(cls.bases) == 1
            base = cls.bases[0]
            assert isinstance(base, ast.Name)
            assert base.ctx == ast.Load
            assert base.id == "Y"
            assert cls.decorator_list is None
        cls = self.get_first_stmt("class X(Y, Z): pass")
        assert len(cls.bases) == 2
        for b in cls.bases:
            assert isinstance(b, ast.Name)
            assert b.ctx == ast.Load

    def test_function(self):
        func = self.get_first_stmt("def f(): pass")
        assert isinstance(func, ast.FunctionDef)
        assert func.name == "f"
        assert len(func.body) == 1
        assert isinstance(func.body[0], ast.Pass)
        assert func.decorator_list is None
        args = func.args
        assert isinstance(args, ast.arguments)
        assert args.args is None
        assert args.defaults is None
        assert args.kwarg is None
        assert args.vararg is None
        assert func.returns is None
        args = self.get_first_stmt("def f(a, b): pass").args
        assert len(args.args) == 2
        a1, a2 = args.args
        assert isinstance(a1, ast.arg)
        assert a1.arg == "a"
        assert isinstance(a2, ast.arg)
        assert a2.arg == "b"
        assert args.vararg is None
        assert args.kwarg is None
        args = self.get_first_stmt("def f(a=b): pass").args
        assert len(args.args) == 1
        arg = args.args[0]
        assert isinstance(arg, ast.arg)
        assert arg.arg == "a"
        assert len(args.defaults) == 1
        default = args.defaults[0]
        assert isinstance(default, ast.Name)
        assert default.id == "b"
        assert default.ctx == ast.Load
        args = self.get_first_stmt("def f(*a): pass").args
        assert not args.args
        assert not args.defaults
        assert args.kwarg is None
        assert args.vararg == "a"
        args = self.get_first_stmt("def f(**a): pass").args
        assert not args.args
        assert not args.defaults
        assert args.vararg is None
        assert args.kwarg == "a"
        args = self.get_first_stmt("def f(a, b, c=d, *e, **f): pass").args
        assert len(args.args) == 3
        for arg in args.args:
            assert isinstance(arg, ast.arg)
        assert len(args.defaults) == 1
        assert isinstance(args.defaults[0], ast.Name)
        assert args.defaults[0].ctx == ast.Load
        assert args.vararg == "e"
        assert args.kwarg == "f"
        input = "def f(a=b, c): pass"
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        assert exc.msg == "non-default argument follows default argument"

    def test_kwonly_arguments(self):
        fn = self.get_first_stmt("def f(a, b, c, *, kwarg): pass")
        assert isinstance(fn, ast.FunctionDef)
        assert len(fn.args.kwonlyargs) == 1
        assert isinstance(fn.args.kwonlyargs[0], ast.arg)
        assert fn.args.kwonlyargs[0].arg == "kwarg"
        assert fn.args.kw_defaults == [None]
        fn = self.get_first_stmt("def f(a, b, c, *args, kwarg): pass")
        assert isinstance(fn, ast.FunctionDef)
        assert len(fn.args.kwonlyargs) == 1
        assert isinstance(fn.args.kwonlyargs[0], ast.arg)
        assert fn.args.kwonlyargs[0].arg == "kwarg"
        assert fn.args.kw_defaults == [None]
        fn = self.get_first_stmt("def f(a, b, c, *, kwarg=2): pass")
        assert isinstance(fn, ast.FunctionDef)
        assert len(fn.args.kwonlyargs) == 1
        assert isinstance(fn.args.kwonlyargs[0], ast.arg)
        assert fn.args.kwonlyargs[0].arg == "kwarg"
        assert len(fn.args.kw_defaults) == 1
        assert isinstance(fn.args.kw_defaults[0], ast.Num)
        input = "def f(p1, *, **k1):  pass"
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        assert exc.msg == "named arguments must follows bare *"

    def test_function_annotation(self):
        func = self.get_first_stmt("def f() -> X: pass")
        assert isinstance(func.returns, ast.Name)
        assert func.returns.id == "X"
        assert func.returns.ctx == ast.Load
        for stmt in "def f(x : 42): pass", "def f(x : 42=a): pass":
            func = self.get_first_stmt(stmt)
            assert isinstance(func.args.args[0].annotation, ast.Num)
        assert isinstance(func.args.defaults[0], ast.Name)
        func = self.get_first_stmt("def f(*x : 42): pass")
        assert isinstance(func.args.varargannotation, ast.Num)
        func = self.get_first_stmt("def f(**kw : 42): pass")
        assert isinstance(func.args.kwargannotation, ast.Num)
        func = self.get_first_stmt("def f(*, kw : 42=a): pass")
        assert isinstance(func.args.kwonlyargs[0].annotation, ast.Num)

    def test_lots_of_kwonly_arguments(self):
        fundef = "def f("
        for i in range(255):
            fundef += "i%d, "%i
        fundef += "*, key=100):\n pass\n"
        py.test.raises(SyntaxError, self.get_first_stmt, fundef)

        fundef2 = "def foo(i,*,"
        for i in range(255):
            fundef2 += "i%d, "%i
        fundef2 += "lastarg):\n  pass\n"
        py.test.raises(SyntaxError, self.get_first_stmt, fundef)

        fundef3 = "def f(i,*,"
        for i in range(253):
            fundef3 += "i%d, "%i
        fundef3 += "lastarg):\n  pass\n"
        self.get_first_stmt(fundef3)

    def test_decorators(self):
        to_examine = (("def f(): pass", ast.FunctionDef),
                      ("class x: pass", ast.ClassDef))
        for stmt, node in to_examine:
            definition = self.get_first_stmt("@dec\n%s" % (stmt,))
            assert isinstance(definition, node)
            assert len(definition.decorator_list) == 1
            dec = definition.decorator_list[0]
            assert isinstance(dec, ast.Name)
            assert dec.id == "dec"
            assert dec.ctx == ast.Load
            definition = self.get_first_stmt("@mod.hi.dec\n%s" % (stmt,))
            assert len(definition.decorator_list) == 1
            dec = definition.decorator_list[0]
            assert isinstance(dec, ast.Attribute)
            assert dec.ctx == ast.Load
            assert dec.attr == "dec"
            assert isinstance(dec.value, ast.Attribute)
            assert dec.value.attr == "hi"
            assert isinstance(dec.value.value, ast.Name)
            assert dec.value.value.id == "mod"
            definition = self.get_first_stmt("@dec\n@dec2\n%s" % (stmt,))
            assert len(definition.decorator_list) == 2
            for dec in definition.decorator_list:
                assert isinstance(dec, ast.Name)
                assert dec.ctx == ast.Load
            assert definition.decorator_list[0].id == "dec"
            assert definition.decorator_list[1].id == "dec2"
            definition = self.get_first_stmt("@dec()\n%s" % (stmt,))
            assert len(definition.decorator_list) == 1
            dec = definition.decorator_list[0]
            assert isinstance(dec, ast.Call)
            assert isinstance(dec.func, ast.Name)
            assert dec.func.id == "dec"
            assert dec.args is None
            assert dec.keywords is None
            assert dec.starargs is None
            assert dec.kwargs is None
            definition = self.get_first_stmt("@dec(a, b)\n%s" % (stmt,))
            assert len(definition.decorator_list) == 1
            dec = definition.decorator_list[0]
            assert isinstance(dec, ast.Call)
            assert dec.func.id == "dec"
            assert len(dec.args) == 2
            assert dec.keywords is None
            assert dec.starargs is None
            assert dec.kwargs is None

    def test_augassign(self):
        aug_assigns = (
            ("+=", ast.Add),
            ("-=", ast.Sub),
            ("/=", ast.Div),
            ("//=", ast.FloorDiv),
            ("%=", ast.Mod),
            ("<<=", ast.LShift),
            (">>=", ast.RShift),
            ("&=", ast.BitAnd),
            ("|=", ast.BitOr),
            ("^=", ast.BitXor),
            ("*=", ast.Mult),
            ("**=", ast.Pow)
        )
        for op, ast_type in aug_assigns:
            input = "x %s 4" % (op,)
            assign = self.get_first_stmt(input)
            assert isinstance(assign, ast.AugAssign)
            assert assign.op is ast_type
            assert isinstance(assign.target, ast.Name)
            assert assign.target.ctx == ast.Store
            assert isinstance(assign.value, ast.Num)

    def test_assign(self):
        assign = self.get_first_stmt("hi = 32")
        assert isinstance(assign, ast.Assign)
        assert len(assign.targets) == 1
        name = assign.targets[0]
        assert isinstance(name, ast.Name)
        assert name.ctx == ast.Store
        value = assign.value
        assert self.space.eq_w(value.n, self.space.wrap(32))
        assign = self.get_first_stmt("hi, = something")
        assert len(assign.targets) == 1
        tup = assign.targets[0]
        assert isinstance(tup, ast.Tuple)
        assert tup.ctx == ast.Store
        assert len(tup.elts) == 1
        assert isinstance(tup.elts[0], ast.Name)
        assert tup.elts[0].ctx == ast.Store

    def test_assign_starred(self):
        assign = self.get_first_stmt("*a, b = x")
        assert isinstance(assign, ast.Assign)
        assert len(assign.targets) == 1
        names = assign.targets[0]
        assert len(names.elts) == 2
        assert isinstance(names.elts[0], ast.Starred)
        assert isinstance(names.elts[1], ast.Name)
        assert isinstance(names.elts[0].value, ast.Name)
        assert names.elts[0].value.id == "a"

    def test_name(self):
        name = self.get_first_expr("hi")
        assert isinstance(name, ast.Name)
        assert name.ctx == ast.Load

    def test_tuple(self):
        tup = self.get_first_expr("()")
        assert isinstance(tup, ast.Tuple)
        assert tup.elts is None
        assert tup.ctx == ast.Load
        tup = self.get_first_expr("(3,)")
        assert len(tup.elts) == 1
        assert self.space.eq_w(tup.elts[0].n, self.space.wrap(3))
        tup = self.get_first_expr("2, 3, 4")
        assert len(tup.elts) == 3

    def test_list(self):
        seq = self.get_first_expr("[]")
        assert isinstance(seq, ast.List)
        assert seq.elts is None
        assert seq.ctx == ast.Load
        seq = self.get_first_expr("[3,]")
        assert len(seq.elts) == 1
        assert self.space.eq_w(seq.elts[0].n, self.space.wrap(3))
        seq = self.get_first_expr("[3]")
        assert len(seq.elts) == 1
        seq = self.get_first_expr("[1, 2, 3, 4, 5]")
        assert len(seq.elts) == 5
        nums = range(1, 6)
        assert [self.space.int_w(n.n) for n in seq.elts] == nums

    def test_dict(self):
        d = self.get_first_expr("{}")
        assert isinstance(d, ast.Dict)
        assert d.keys is None
        assert d.values is None
        d = self.get_first_expr("{4 : x, y : 7}")
        assert len(d.keys) == len(d.values) == 2
        key1, key2 = d.keys
        assert isinstance(key1, ast.Num)
        assert isinstance(key2, ast.Name)
        assert key2.ctx == ast.Load
        v1, v2 = d.values
        assert isinstance(v1, ast.Name)
        assert v1.ctx == ast.Load
        assert isinstance(v2, ast.Num)

    def test_set(self):
        s = self.get_first_expr("{1}")
        assert isinstance(s, ast.Set)
        assert len(s.elts) == 1
        assert isinstance(s.elts[0], ast.Num)
        assert self.space.eq_w(s.elts[0].n, self.space.wrap(1))
        s = self.get_first_expr("{0, 1, 2, 3, 4, 5}")
        assert isinstance(s, ast.Set)
        assert len(s.elts) == 6
        for i, elt in enumerate(s.elts):
            assert isinstance(elt, ast.Num)
            assert self.space.eq_w(elt.n, self.space.wrap(i))

    def test_set_context(self):
        tup = self.get_ast("(a, b) = c").body[0].targets[0]
        assert all(elt.ctx == ast.Store for elt in tup.elts)
        seq = self.get_ast("[a, b] = c").body[0].targets[0]
        assert all(elt.ctx == ast.Store for elt in seq.elts)
        invalid_stores = (
            ("(lambda x: x)", "lambda"),
            ("f()", "function call"),
            ("~x", "operator"),
            ("+x", "operator"),
            ("-x", "operator"),
            ("(x or y)", "operator"),
            ("(x and y)", "operator"),
            ("(not g)", "operator"),
            ("(x for y in g)", "generator expression"),
            ("(yield x)", "yield expression"),
            ("[x for y in g]", "list comprehension"),
            ("{x for x in z}", "set comprehension"),
            ("{x : x for x in z}", "dict comprehension"),
            ("'str'", "literal"),
            ("b'bytes'", "literal"),
            ("()", "()"),
            ("23", "literal"),
            ("{}", "literal"),
            ("{1, 2, 3}", "literal"),
            ("(x > 4)", "comparison"),
            ("(x if y else a)", "conditional expression"),
            ("...", "Ellipsis"),
        )
        test_contexts = (
            ("assign to", "%s = 23"),
            ("delete", "del %s")
        )
        for ctx_type, template in test_contexts:
            for expr, type_str in invalid_stores:
                input = template % (expr,)
                exc = py.test.raises(SyntaxError, self.get_ast, input).value
                assert exc.msg == "can't %s %s" % (ctx_type, type_str)

    def test_assignment_to_forbidden_names(self):
        invalid = (
            "%s = x",
            "%s, x = y",
            "def %s(): pass",
            "class %s(): pass",
            "def f(%s): pass",
            "def f(%s=x): pass",
            "def f(*%s): pass",
            "def f(**%s): pass",
            "f(%s=x)",
            "with x as %s: pass",
            "import %s",
            "import x as %s",
            "from x import %s",
            "from x import y as %s",
            "for %s in x: pass",
        )
        for name in "__debug__",:
            for template in invalid:
                input = template % (name,)
                exc = py.test.raises(SyntaxError, self.get_ast, input).value
                assert exc.msg == "cannot assign to %s" % (name,)

    def test_lambda(self):
        lam = self.get_first_expr("lambda x: expr")
        assert isinstance(lam, ast.Lambda)
        args = lam.args
        assert isinstance(args, ast.arguments)
        assert args.vararg is None
        assert args.kwarg is None
        assert not args.defaults
        assert len(args.args) == 1
        assert isinstance(args.args[0], ast.arg)
        assert isinstance(lam.body, ast.Name)
        lam = self.get_first_expr("lambda: True")
        args = lam.args
        assert not args.args
        lam = self.get_first_expr("lambda x=x: y")
        assert len(lam.args.args) == 1
        assert len(lam.args.defaults) == 1
        assert isinstance(lam.args.defaults[0], ast.Name)
        input = "f(lambda x: x[0] = y)"
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        assert exc.msg == "lambda cannot contain assignment"

    def test_ifexp(self):
        ifexp = self.get_first_expr("x if y else g")
        assert isinstance(ifexp, ast.IfExp)
        assert isinstance(ifexp.test, ast.Name)
        assert ifexp.test.ctx == ast.Load
        assert isinstance(ifexp.body, ast.Name)
        assert ifexp.body.ctx == ast.Load
        assert isinstance(ifexp.orelse, ast.Name)
        assert ifexp.orelse.ctx == ast.Load

    def test_boolop(self):
        for ast_type, op in ((ast.And, "and"), (ast.Or, "or")):
            bo = self.get_first_expr("x %s a" % (op,))
            assert isinstance(bo, ast.BoolOp)
            assert bo.op == ast_type
            assert len(bo.values) == 2
            assert isinstance(bo.values[0], ast.Name)
            assert isinstance(bo.values[1], ast.Name)
            bo = self.get_first_expr("x %s a %s b" % (op, op))
            assert bo.op == ast_type
            assert len(bo.values) == 3

    def test_not(self):
        n = self.get_first_expr("not x")
        assert isinstance(n, ast.UnaryOp)
        assert n.op == ast.Not
        assert isinstance(n.operand, ast.Name)
        assert n.operand.ctx == ast.Load

    def test_comparison(self):
        compares = (
            (">", ast.Gt),
            (">=", ast.GtE),
            ("<", ast.Lt),
            ("<=", ast.LtE),
            ("==", ast.Eq),
            ("!=", ast.NotEq),
            ("in", ast.In),
            ("is", ast.Is),
            ("is not", ast.IsNot),
            ("not in", ast.NotIn)
        )
        for op, ast_type in compares:
            comp = self.get_first_expr("x %s y" % (op,))
            assert isinstance(comp, ast.Compare)
            assert isinstance(comp.left, ast.Name)
            assert comp.left.ctx == ast.Load
            assert len(comp.ops) == 1
            assert comp.ops[0] == ast_type
            assert len(comp.comparators) == 1
            assert isinstance(comp.comparators[0], ast.Name)
            assert comp.comparators[0].ctx == ast.Load
        # Just for fun let's randomly combine operators. :)
        for j in range(10):
            vars = string.ascii_letters[:random.randint(3, 7)]
            ops = [random.choice(compares) for i in range(len(vars) - 1)]
            input = vars[0]
            for i, (op, _) in enumerate(ops):
                input += " %s %s" % (op, vars[i + 1])
            comp = self.get_first_expr(input)
            assert comp.ops == [tup[1] for tup in ops]
            names = comp.left.id + "".join(n.id for n in comp.comparators)
            assert names == vars

    def test_flufl(self):
        source = "x <> y"
        raises(SyntaxError, self.get_ast, source)
        comp = self.get_first_expr(source,
                                   flags=consts.CO_FUTURE_BARRY_AS_BDFL)
        assert isinstance(comp, ast.Compare)
        assert isinstance(comp.left, ast.Name)
        assert comp.left.ctx == ast.Load
        assert len(comp.ops) == 1
        assert comp.ops[0] == ast.NotEq
        assert len(comp.comparators) == 1
        assert isinstance(comp.comparators[0], ast.Name)
        assert comp.comparators[0].ctx == ast.Load

    def test_binop(self):
        binops = (
            ("|", ast.BitOr),
            ("&", ast.BitAnd),
            ("^", ast.BitXor),
            ("<<", ast.LShift),
            (">>", ast.RShift),
            ("+", ast.Add),
            ("-", ast.Sub),
            ("/", ast.Div),
            ("*", ast.Mult),
            ("//", ast.FloorDiv),
            ("%", ast.Mod)
        )
        for op, ast_type in binops:
            bin = self.get_first_expr("a %s b" % (op,))
            assert isinstance(bin, ast.BinOp)
            assert bin.op == ast_type
            assert isinstance(bin.left, ast.Name)
            assert isinstance(bin.right, ast.Name)
            assert bin.left.ctx == ast.Load
            assert bin.right.ctx == ast.Load
            bin = self.get_first_expr("a %s b %s c" % (op, op))
            assert isinstance(bin.left, ast.BinOp)
            assert bin.left.op == ast_type
            assert isinstance(bin.right, ast.Name)

    def test_yield(self):
        expr = self.get_first_expr("yield")
        assert isinstance(expr, ast.Yield)
        assert expr.value is None
        expr = self.get_first_expr("yield x")
        assert isinstance(expr.value, ast.Name)
        assign = self.get_first_stmt("x = yield x")
        assert isinstance(assign, ast.Assign)
        assert isinstance(assign.value, ast.Yield)

    def test_yield_from(self):
        expr = self.get_first_expr("yield from x")
        assert isinstance(expr, ast.YieldFrom)
        assert isinstance(expr.value, ast.Name)

    def test_unaryop(self):
        unary_ops = (
            ("+", ast.UAdd),
            ("-", ast.USub),
            ("~", ast.Invert)
        )
        for op, ast_type in unary_ops:
            unary = self.get_first_expr("%sx" % (op,))
            assert isinstance(unary, ast.UnaryOp)
            assert unary.op == ast_type
            assert isinstance(unary.operand, ast.Name)
            assert unary.operand.ctx == ast.Load

    def test_power(self):
        power = self.get_first_expr("x**5")
        assert isinstance(power, ast.BinOp)
        assert power.op == ast.Pow
        assert isinstance(power.left , ast.Name)
        assert power.left.ctx == ast.Load
        assert isinstance(power.right, ast.Num)

    def test_call(self):
        call = self.get_first_expr("f()")
        assert isinstance(call, ast.Call)
        assert call.args is None
        assert call.keywords is None
        assert call.starargs is None
        assert call.kwargs is None
        assert isinstance(call.func, ast.Name)
        assert call.func.ctx == ast.Load
        call = self.get_first_expr("f(2, 3)")
        assert len(call.args) == 2
        assert isinstance(call.args[0], ast.Num)
        assert isinstance(call.args[1], ast.Num)
        assert call.keywords is None
        assert call.starargs is None
        assert call.kwargs is None
        call = self.get_first_expr("f(a=3)")
        assert call.args is None
        assert len(call.keywords) == 1
        keyword = call.keywords[0]
        assert isinstance(keyword, ast.keyword)
        assert keyword.arg == "a"
        assert isinstance(keyword.value, ast.Num)
        call = self.get_first_expr("f(*a, **b)")
        assert call.args is None
        assert isinstance(call.starargs, ast.Name)
        assert call.starargs.id == "a"
        assert call.starargs.ctx == ast.Load
        assert isinstance(call.kwargs, ast.Name)
        assert call.kwargs.id == "b"
        assert call.kwargs.ctx == ast.Load
        call = self.get_first_expr("f(a, b, x=4, *m, **f)")
        assert len(call.args) == 2
        assert isinstance(call.args[0], ast.Name)
        assert isinstance(call.args[1], ast.Name)
        assert len(call.keywords) == 1
        assert call.keywords[0].arg == "x"
        assert call.starargs.id == "m"
        assert call.kwargs.id == "f"
        call = self.get_first_expr("f(x for x in y)")
        assert len(call.args) == 1
        assert isinstance(call.args[0], ast.GeneratorExp)
        input = "f(x for x in y, 1)"
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        assert exc.msg == "Generator expression must be parenthesized if not " \
            "sole argument"
        many_args = ", ".join("x%i" % i for i in range(256))
        input = "f(%s)" % (many_args,)
        exc = py.test.raises(SyntaxError, self.get_ast, input).value
        assert exc.msg == "more than 255 arguments"
        exc = py.test.raises(SyntaxError, self.get_ast, "f((a+b)=c)").value
        assert exc.msg == "keyword can't be an expression"
        exc = py.test.raises(SyntaxError, self.get_ast, "f(a=c, a=d)").value
        assert exc.msg == "keyword argument repeated"
        exc = py.test.raises(SyntaxError, self.get_ast, "f(x, *a, b)").value
        assert exc.msg == "only named arguments may follow *expression"

    def test_attribute(self):
        attr = self.get_first_expr("x.y")
        assert isinstance(attr, ast.Attribute)
        assert isinstance(attr.value, ast.Name)
        assert attr.value.ctx == ast.Load
        assert attr.attr == "y"
        assert attr.ctx == ast.Load
        assign = self.get_first_stmt("x.y = 54")
        assert isinstance(assign, ast.Assign)
        assert len(assign.targets) == 1
        attr = assign.targets[0]
        assert isinstance(attr, ast.Attribute)
        assert attr.value.ctx == ast.Load
        assert attr.ctx == ast.Store

    def test_subscript_and_slices(self):
        sub = self.get_first_expr("x[y]")
        assert isinstance(sub, ast.Subscript)
        assert isinstance(sub.value, ast.Name)
        assert sub.value.ctx == ast.Load
        assert sub.ctx == ast.Load
        assert isinstance(sub.slice, ast.Index)
        assert isinstance(sub.slice.value, ast.Name)
        slc = self.get_first_expr("x[:]").slice
        assert slc.upper is None
        assert slc.lower is None
        assert slc.step is None
        slc = self.get_first_expr("x[::]").slice
        assert slc.upper is None
        assert slc.lower is None
        assert slc.step is None
        slc = self.get_first_expr("x[1:]").slice
        assert isinstance(slc.lower, ast.Num)
        assert slc.upper is None
        assert slc.step is None
        slc = self.get_first_expr("x[1::]").slice
        assert isinstance(slc.lower, ast.Num)
        assert slc.upper is None
        assert slc.step is None
        slc = self.get_first_expr("x[:2]").slice
        assert slc.lower is None
        assert isinstance(slc.upper, ast.Num)
        assert slc.step is None
        slc = self.get_first_expr("x[:2:]").slice
        assert slc.lower is None
        assert isinstance(slc.upper, ast.Num)
        assert slc.step is None
        slc = self.get_first_expr("x[2:2]").slice
        assert isinstance(slc.lower, ast.Num)
        assert isinstance(slc.upper, ast.Num)
        assert slc.step is None
        slc = self.get_first_expr("x[2:2:]").slice
        assert isinstance(slc.lower, ast.Num)
        assert isinstance(slc.upper, ast.Num)
        assert slc.step is None
        slc = self.get_first_expr("x[::2]").slice
        assert slc.lower is None
        assert slc.upper is None
        assert isinstance(slc.step, ast.Num)
        slc = self.get_first_expr("x[2::2]").slice
        assert isinstance(slc.lower, ast.Num)
        assert slc.upper is None
        assert isinstance(slc.step, ast.Num)
        slc = self.get_first_expr("x[:2:2]").slice
        assert slc.lower is None
        assert isinstance(slc.upper, ast.Num)
        assert isinstance(slc.step, ast.Num)
        slc = self.get_first_expr("x[1:2:3]").slice
        for field in (slc.lower, slc.upper, slc.step):
            assert isinstance(field, ast.Num)
        sub = self.get_first_expr("x[1,2,3]")
        slc = sub.slice
        assert isinstance(slc, ast.Index)
        assert isinstance(slc.value, ast.Tuple)
        assert len(slc.value.elts) == 3
        assert slc.value.ctx == ast.Load
        slc = self.get_first_expr("x[1,3:4]").slice
        assert isinstance(slc, ast.ExtSlice)
        assert len(slc.dims) == 2
        complex_slc = slc.dims[1]
        assert isinstance(complex_slc, ast.Slice)
        assert isinstance(complex_slc.lower, ast.Num)
        assert isinstance(complex_slc.upper, ast.Num)
        assert complex_slc.step is None

    def test_ellipsis(self):
        e = self.get_first_expr("...")
        assert isinstance(e, ast.Ellipsis)
        sub = self.get_first_expr("x[...]")
        assert isinstance(sub.slice.value, ast.Ellipsis)

    def test_string(self):
        space = self.space
        s = self.get_first_expr("'hi'")
        assert isinstance(s, ast.Str)
        assert space.eq_w(s.s, space.wrap("hi"))
        s = self.get_first_expr("'hi' ' implicitly' ' extra'")
        assert isinstance(s, ast.Str)
        assert space.eq_w(s.s, space.wrap("hi implicitly extra"))
        s = self.get_first_expr("b'hi' b' implicitly' b' extra'")
        assert isinstance(s, ast.Bytes)
        assert space.eq_w(s.s, space.wrapbytes("hi implicitly extra"))
        raises(SyntaxError, self.get_first_expr, "b'hello' 'world'")
        sentence = u"Die Männer ärgen sich!"
        source = u"# coding: utf-7\nstuff = '%s'" % (sentence,)
        info = pyparse.CompileInfo("<test>", "exec")
        tree = self.parser.parse_source(source.encode("utf-7"), info)
        assert info.encoding == "utf-7"
        s = ast_from_node(space, tree, info).body[0].value
        assert isinstance(s, ast.Str)
        assert space.eq_w(s.s, space.wrap(sentence))

    def test_string_pep3120(self):
        space = self.space
        japan = u'日本'
        source = u"foo = '%s'" % japan
        info = pyparse.CompileInfo("<test>", "exec")
        tree = self.parser.parse_source(source.encode("utf-8"), info)
        assert info.encoding == "utf-8"
        s = ast_from_node(space, tree, info).body[0].value
        assert isinstance(s, ast.Str)
        assert space.eq_w(s.s, space.wrap(japan))

    def test_name_pep3131(self):
        assign = self.get_first_stmt("日本 = 32")
        assert isinstance(assign, ast.Assign)
        name = assign.targets[0]
        assert isinstance(name, ast.Name)
        assert name.id == u"日本".encode('utf-8')

    def test_function_pep3131(self):
        fn = self.get_first_stmt("def µ(µ='foo'): pass")
        assert isinstance(fn, ast.FunctionDef)
        # µ normalized to NFKC
        expected = u'\u03bc'.encode('utf-8')
        assert fn.name == expected
        assert fn.args.args[0].arg == expected

    def test_import_pep3131(self):
        im = self.get_first_stmt("from packageµ import modµ as µ")
        assert isinstance(im, ast.ImportFrom)
        expected = u'\u03bc'.encode('utf-8')
        assert im.module == 'package' + expected
        alias = im.names[0]
        assert alias.name == 'mod' + expected
        assert alias.asname == expected

    def test_issue3574(self):
        space = self.space
        source = u'# coding: Latin-1\nu = "Ç"\n'
        info = pyparse.CompileInfo("<test>", "exec")
        tree = self.parser.parse_source(source.encode("Latin-1"), info)
        assert info.encoding == "iso-8859-1"
        s = ast_from_node(space, tree, info).body[0].value
        assert isinstance(s, ast.Str)
        assert space.eq_w(s.s, space.wrap(u'Ç'))
 
    def test_string_bug(self):
        space = self.space
        source = '# -*- encoding: utf8 -*-\nstuff = "x \xc3\xa9 \\n"\n'
        info = pyparse.CompileInfo("<test>", "exec")
        tree = self.parser.parse_source(source, info)
        assert info.encoding == "utf8"
        s = ast_from_node(space, tree, info).body[0].value
        assert isinstance(s, ast.Str)
        assert space.eq_w(s.s, space.wrap(u'x \xe9 \n'))

    def test_number(self):
        def get_num(s):
            node = self.get_first_expr(s)
            assert isinstance(node, ast.Num)
            value = node.n
            assert isinstance(value, W_Root)
            return value
        space = self.space
        assert space.eq_w(get_num("32"), space.wrap(32))
        assert space.eq_w(get_num("32.5"), space.wrap(32.5))
        assert space.eq_w(get_num("2"), space.wrap(2))
        assert space.eq_w(get_num("13j"), space.wrap(13j))
        assert space.eq_w(get_num("13J"), space.wrap(13J))
        assert space.eq_w(get_num("0o53"), space.wrap(053))
        assert space.eq_w(get_num("0o0053"), space.wrap(053))
        for num in ("0x53", "0X53", "0x0000053", "0X00053"):
            assert space.eq_w(get_num(num), space.wrap(0x53))
        assert space.eq_w(get_num("0Xb0d2"), space.wrap(0xb0d2))
        assert space.eq_w(get_num("0X53"), space.wrap(0x53))
        assert space.eq_w(get_num("0"), space.wrap(0))
        assert space.eq_w(get_num("00000"), space.wrap(0))
        for num in ("0o53", "0O53", "0o0000053", "0O00053"):
            assert space.eq_w(get_num(num), space.wrap(053))
        for num in ("0b00101", "0B00101", "0b101", "0B101"):
            assert space.eq_w(get_num(num), space.wrap(5))

        py.test.raises(SyntaxError, self.get_ast, "0x")
        py.test.raises(SyntaxError, self.get_ast, "0b")
        py.test.raises(SyntaxError, self.get_ast, "0o")
        py.test.raises(SyntaxError, self.get_ast, "32L")
        py.test.raises(SyntaxError, self.get_ast, "32l")
        py.test.raises(SyntaxError, self.get_ast, "0L")
        py.test.raises(SyntaxError, self.get_ast, "-0xAAAAAAL")
        py.test.raises(SyntaxError, self.get_ast, "053")
        py.test.raises(SyntaxError, self.get_ast, "00053")

    def check_comprehension(self, brackets, ast_type):
        def brack(s):
            return brackets % s
        gen = self.get_first_expr(brack("x for x in y"))
        assert isinstance(gen, ast_type)
        assert isinstance(gen.elt, ast.Name)
        assert gen.elt.ctx == ast.Load
        assert len(gen.generators) == 1
        comp = gen.generators[0]
        assert isinstance(comp, ast.comprehension)
        assert comp.ifs is None
        assert isinstance(comp.target, ast.Name)
        assert isinstance(comp.iter, ast.Name)
        assert comp.target.ctx == ast.Store
        gen = self.get_first_expr(brack("x for x in y if w"))
        comp = gen.generators[0]
        assert len(comp.ifs) == 1
        test = comp.ifs[0]
        assert isinstance(test, ast.Name)
        gen = self.get_first_expr(brack("x for x, in y if w"))
        tup = gen.generators[0].target
        assert isinstance(tup, ast.Tuple)
        assert len(tup.elts) == 1
        assert tup.ctx == ast.Store
        gen = self.get_first_expr(brack("a for w in x for m in p if g"))
        gens = gen.generators
        assert len(gens) == 2
        comp1, comp2 = gens
        assert comp1.ifs is None
        assert len(comp2.ifs) == 1
        assert isinstance(comp2.ifs[0], ast.Name)
        gen = self.get_first_expr(brack("x for x in y if m if g"))
        comps = gen.generators
        assert len(comps) == 1
        assert len(comps[0].ifs) == 2
        if1, if2 = comps[0].ifs
        assert isinstance(if1, ast.Name)
        assert isinstance(if2, ast.Name)
        gen = self.get_first_expr(brack("x for x in y or z"))
        comp = gen.generators[0]
        assert isinstance(comp.iter, ast.BoolOp)
        assert len(comp.iter.values) == 2
        assert isinstance(comp.iter.values[0], ast.Name)
        assert isinstance(comp.iter.values[1], ast.Name)

    def test_genexp(self):
        self.check_comprehension("(%s)", ast.GeneratorExp)

    def test_listcomp(self):
        self.check_comprehension("[%s]", ast.ListComp)

    def test_setcomp(self):
        self.check_comprehension("{%s}", ast.SetComp)

    def test_dictcomp(self):
        gen = self.get_first_expr("{x : z for x in y}")
        assert isinstance(gen, ast.DictComp)
        assert isinstance(gen.key, ast.Name)
        assert gen.key.ctx == ast.Load
        assert isinstance(gen.value, ast.Name)
        assert gen.value.ctx == ast.Load
        assert len(gen.generators) == 1
        comp = gen.generators[0]
        assert isinstance(comp, ast.comprehension)
        assert comp.ifs is None
        assert isinstance(comp.target, ast.Name)
        assert isinstance(comp.iter, ast.Name)
        assert comp.target.ctx == ast.Store
        gen = self.get_first_expr("{x : z for x in y if w}")
        comp = gen.generators[0]
        assert len(comp.ifs) == 1
        test = comp.ifs[0]
        assert isinstance(test, ast.Name)
        gen = self.get_first_expr("{x : z for x, in y if w}")
        tup = gen.generators[0].target
        assert isinstance(tup, ast.Tuple)
        assert len(tup.elts) == 1
        assert tup.ctx == ast.Store
        gen = self.get_first_expr("{a : b for w in x for m in p if g}")
        gens = gen.generators
        assert len(gens) == 2
        comp1, comp2 = gens
        assert comp1.ifs is None
        assert len(comp2.ifs) == 1
        assert isinstance(comp2.ifs[0], ast.Name)
        gen = self.get_first_expr("{x : z for x in y if m if g}")
        comps = gen.generators
        assert len(comps) == 1
        assert len(comps[0].ifs) == 2
        if1, if2 = comps[0].ifs
        assert isinstance(if1, ast.Name)
        assert isinstance(if2, ast.Name)

    def test_cpython_issue12983(self):
        raises(SyntaxError, self.get_ast, r"""b'\x'""")
        raises(SyntaxError, self.get_ast, r"""b'\x0'""")
