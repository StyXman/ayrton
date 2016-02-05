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

import os
import sys
import importlib
import ast
import logging
import dis
import traceback
import linecache

# patch logging so we have debug2 and debug3
import ayrton.utils

log_format= "%(asctime)s %(name)16s:%(lineno)-4d (%(funcName)-21s) %(levelname)-8s %(message)s"
date_format= "%H:%M:%S"

# uncomment one of these for way too much debugging :)
# logging.basicConfig(filename='ayrton.%d.log' % os.getpid (), level=logging.DEBUG, format=log_format, datefmt=date_format)
# logging.basicConfig(filename='ayrton.log', level=logging.DEBUG, format=log_format, datefmt=date_format)
logger= logging.getLogger ('ayrton')

# things that have to be defined before importing ayton.execute :(
# singleton needed so the functions can access the runner
runner= None

from ayrton.castt import CrazyASTTransformer
from ayrton.execute import o, Command, Capture, CommandFailed
from ayrton.parser.pyparser.pyparse import CompileInfo, PythonParser
from ayrton.parser.astcompiler.astbuilder import ast_from_node
from ayrton.ast_pprinter import pprint

__version__= '0.7'


class ExecParams:
    def __init__ (self, **kwargs):
        # defaults
        self.trace= False

        self.__dict__.update (kwargs)


def parse (script, file_name=''):
    parser= PythonParser (None)
    info= CompileInfo (file_name, 'exec')
    return ast_from_node (None, parser.parse_source (script, info), info)


class Environment (dict):
    def __init__ (self, *args, **kwargs):
        super ().__init__ (*args, **kwargs)

        self.polute ()


    def polute (self):
        self.update (__builtins__)
        # weed out some stuff
        for weed in ('copyright', '__doc__', 'help', '__package__', 'credits',
                     'license', '__name__', 'quit', 'exit'):
            if weed in self:
                del self[weed]

        # these functions will be loaded from each module and put in the globals
        # tuples (src, dst) renames function src to dst
        ayrton_builtins= {
            'os': [ ('getcwd', 'pwd'), 'uname', 'listdir', ],
            'os.path': [ 'abspath', 'basename', 'commonprefix', 'dirname',  ],
            'time': [ 'sleep', ],
            'sys': [ 'exit', ],  # argv is handled just before execution

            'ayrton.file_test': [ '_a', '_b', '_c', '_d', '_e', '_f', '_g', '_h',
                                  '_k', '_p', '_r', '_s', '_u', '_w', '_x', '_L',
                                  '_N', '_S', '_nt', '_ot' ],
            'ayrton.expansion': [ 'bash', ],
            'ayrton.functions': [ 'cd', ('cd', 'chdir'), 'export', 'option', 'run',
                                   'shift', 'unset', ],
            'ayrton.execute': [ 'o', 'Capture', 'CommandFailed', 'CommandNotFound',
                                'Pipe', 'Command'],
            'ayrton.remote': [ 'remote' ]
            }

        for module, functions in ayrton_builtins.items ():
            m= importlib.import_module (module)
            for function in functions:
                if type (function)==tuple:
                    src, dst= function
                else:
                    src= function
                    dst= function

                self[dst]= getattr (m, src)

        # now the IO files
        for std in ('stdin', 'stdout', 'stderr'):
            self[std]= getattr (sys, std).buffer


class Ayrton (object):
    def __init__ (self, g=None, l=None, **kwargs):
        logger.debug ('===========================================================')
        logger.debug ('new interpreter')
        logger.debug3 ('globals: %s', ayrton.utils.dump_dict (g))
        logger.debug3 ('locals: %s', ayrton.utils.dump_dict (l))

        self.globals= Environment ()
        if g is not None:
            self.globals.update (g)
        self.globals.update (kwargs)

        if l is None:
            # If exec gets two separate objects as globals and locals,
            # the code will be executed as if it were embedded in a class definition.
            # and this happens:
            """
            In [7]: source='''import math
            ...: def foo ():
            ...:     math.floor (1.1, )
            ...:
            ...: foo()'''

            In [8]: import ast
            In [9]: t= ast.parse (source)
            In [10]: c= compile (t, 'foo.py', 'exec')
            In [11]: exec (c, {}, {})
            ---------------------------------------------------------------------------
            NameError                                 Traceback (most recent call last)
            <ipython-input-11-3a2844c232c1> in <module>()
            ----> 1 exec (c, {}, {})
            /home/mdione/src/projects/ayrton/foo.py in <module>()
            /home/mdione/src/projects/ayrton/foo.py in foo()
            NameError: name 'math' is not defined
            """
            self.locals= self.globals
        else:
            self.locals= l

        self.options= {}
        self.pending_children= []
        self.file_name= None
        self.script= None
        self.params= ExecParams ()

        # HACK to update the singleton
        # this might break if we implement subinstances
        global runner
        runner= self


    def run_file (self, file_name, argv=None, params=None):
        # it's a pity that parse() does not accept a file as input
        # so we could avoid reading the whole file
        # and now we read it anyways in the case of tracing
        logger.debug ('running from file %s', file_name)

        f= open (file_name)
        script= f.read ()
        f.close ()

        return self.run_script (script, file_name, argv, params)


    def run_script (self, script, file_name, argv=None, params=None):
        logger.debug ('running script:\n-----------\n%s\n-----------', script)
        self.file_name= file_name
        self.script= script.split ('\n')

        # up to this point the script is the whole script in one string
        # because parse() needs it that way
        tree= parse (script, file_name)
        # TODO: self.locals?
        tree= CrazyASTTransformer (self.globals, file_name).modify (tree)

        return self.run_tree (tree, file_name, argv, params)


    def run_tree (self, tree, file_name, argv=None, params=None):
        logger.debug2 ('AST: %s', ast.dump (tree))
        logger.debug2 ('code: \n%s', pprint (tree))

        if params is not None:
            # we delay this assignment down to here because run_file(),
            # run_script() and run_tree() are entry points
            self.params= params

        code= compile (tree, file_name, 'exec')
        return self.run_code (code, file_name, argv)


    def run_code (self, code, file_name, argv=None):
        if logger.parent.level<=logging.DEBUG2:
            logger.debug2 ('------------------')
            logger.debug2 ('main (gobal) code:')
            handler= logger.parent.handlers[0]

            handler.acquire ()
            dis.dis (code, file=handler.stream)
            handler.release ()

            for inst in dis.Bytecode (code):
                if inst.opname=='LOAD_CONST':
                    if type (inst.argval)==type (code):
                        logger.debug ('------------------')
                        handler.acquire ()
                        dis.dis (inst.argval, file=handler.stream)
                        handler.release ()
                    elif type (inst.argval)==str:
                        logger.debug ("last function is called: %s", inst.argval)

        # prepare environment
        self.globals.update (os.environ)

        logger.debug (argv)
        if argv is None:
            argv= [ file_name ]
        self.globals['argv']= argv

        '''
        exec(): If only globals is provided, it must be a dictionary, which will
        be used for both the global and the local variables. If globals and locals
        are given, they are used for the global and local variables, respectively.
        If provided, locals can be any mapping object. Remember that at module
        level, globals and locals are the same dictionary. If exec gets two
        separate objects as globals and locals, the code will be executed as if
        it were embedded in a class definition.

        If the globals dictionary does not contain a value for the key __builtins__,
        a reference to the dictionary of the built-in module builtins is inserted
        under that key. That way you can control what builtins are available to
        the executed code by inserting your own __builtins__ dictionary into
        globals before passing it to exec().

        The default locals act as described for function locals() below:
        modifications to the default locals dictionary should not be attempted.
        Pass an explicit locals dictionary if you need to see effects of the code
        on locals after function exec() returns.

        locals(): Update and return a dictionary representing the current local
        symbol table. Free variables are returned by locals() when it is called
        in function blocks, but not in class blocks.

        The contents of this dictionary should not be modified; changes may not
        affect the values of local and free variables used by the interpreter.
        '''
        error= None
        try:
            logger.debug3 ('globals for script: %s', ayrton.utils.dump_dict (self.globals))
            if self.params.trace:
                sys.settrace (self.global_tracer)
            exec (code, self.globals, self.locals)
        except Exception as e:
            logger.debug ('script finished by Exception')
            logger.debug (traceback.format_exc ())
            error= e
        finally:
            sys.settrace (None)

        logger.debug3 ('globals at script exit: %s', ayrton.utils.dump_dict (self.globals))
        logger.debug3 ('locals at script exit: %s', ayrton.utils.dump_dict (self.locals))
        result= self.locals.get ('ayrton_return_value', None)
        logger.debug ('ayrton_return_value: %r', result)

        if error is not None:
            raise error

        return result


    def wait_for_pending_children (self):
        for i in range (len (self.pending_children)):
            child= self.pending_children.pop (0)
            child.wait ()


    def global_tracer (self, frame, event, arg):
        """"""
        logger.debug2 ('global_tracer: %s', event)
        if event in ('call', 'line'):
            return self.local_tracer
        else:
            return None


    def local_tracer (self, frame, event, arg):
        if event=='line':
            filename= frame.f_code.co_filename
            if filename==self.file_name:
                lineno= frame.f_lineno

                line= linecache.getline (filename, lineno)
                if line=='':
                    line= self.script[lineno-1]  # line numbers start at 1

                logger.debug2 ('trace e: %s, f: %s, n: %d, l: %s', event, filename, lineno, line)
                print ("+ %s" % line, end='', file=sys.stderr)  # line already has a \n


def run_tree (tree, g, l):
    """main entry point for remote()"""
    runner= Ayrton (g=g, l=l)
    return runner.run_tree (tree, 'unknown_tree')

def run_file_or_script (script=None, file_name='script_from_command_line',
                        argv=None, params=None, **kwargs):
    """Main entry point for bin/ayrton and unittests."""
    runner= Ayrton (**kwargs)

    if params is None:
        params= ExecParams ()

    if script is None:
        v= runner.run_file (file_name, argv, params)
    else:
        v= runner.run_script (script, file_name, argv, params)

    return v

# backwards support for unit tests
main= run_file_or_script
