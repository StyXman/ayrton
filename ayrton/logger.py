# -*- coding: utf-8 -*-

# (c) 2017 Marcos Dione <mdione@grulic.org.ar>

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

import os.path
import logging
import io

# NOTE: you can't log in this module!
# of course you can?
logger= logging.getLogger(__file__)


# shamelessly copied from py3.6's logging/__init__.py
# NOTE: update as needed

def foo():
    pass

_srcfile = os.path.normcase(foo.__code__.co_filename)

class Logger(logging.Logger):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    # ditto
    def findCaller(self, stack_info=False, callers=0):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name. Not only ignore this class's
        and logger's source, but also as many callers as requested.
        """
        f = logging.currentframe()
        #On some versions of IronPython, currentframe() returns None if
        #IronPython isn't run with -X:Frames.
        if f is not None:
            if callers > 0:
                # yes we can!
                co = f.f_code
                logger.debug2("%s:%s", co.co_filename, co.co_name)
            f = f.f_back
        rv = "(unknown file)", 0, "(unknown function)", None
        countdown = callers
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if callers > 0:
                # yes we can!
                logger.debug2("%s:%s", co.co_filename, co.co_name)
            if filename in(_srcfile, logging._srcfile):
                f = f.f_back
                continue
            if countdown > 0:
                f = f.f_back
                countdown -= 1
                continue
            sinfo = None
            if stack_info:
                sio = io.StringIO()
                sio.write('Stack (most recent call last):\n')
                traceback.print_stack(f, file=sio)
                sinfo = sio.getvalue()
                if sinfo[-1] == '\n':
                    sinfo = sinfo[:-1]
                sio.close()
            rv = (co.co_filename, f.f_lineno, co.co_name, sinfo)
            break
        return rv


    # ditto
    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False,
             callers=0):
        """
        Low-level logging routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.
        """
        sinfo = None
        if _srcfile:
            #IronPython doesn't track Python frames, so findCaller raises an
            #exception on some versions of IronPython. We trap it here so that
            #IronPython can use logging.
            try:
                fn, lno, func, sinfo = self.findCaller(stack_info, callers)
            except ValueError: # pragma: no cover
                fn, lno, func = "(unknown file)", 0, "(unknown function)"
        else: # pragma: no cover
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if isinstance(exc_info, BaseException):
                exc_info = (type(exc_info), exc_info, exc_info.__traceback__)
            elif not isinstance(exc_info, tuple):
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args,
                                 exc_info, func, extra, sinfo)
        self.handle(record)


# insert this code in logging's infra
logging.setLoggerClass(Logger)
