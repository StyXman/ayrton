import io
import itertools
import os
import sys
import traceback
from errno import EINTR

from ayrton.parser import debug


AUTO_DEBUG = os.getenv('PYPY_DEBUG')
RECORD_INTERPLEVEL_TRACEBACK = True

def strerror(errno):
    """Translate an error code to a message string."""
    from pypy.module._codecs.locale import str_decode_locale_surrogateescape
    return str_decode_locale_surrogateescape(os.strerror(errno))

class OperationError(Exception):
    """Interpreter-level exception that signals an exception that should be
    sent to the application level.

    OperationError instances have three attributes (and no .args),
    w_type, _w_value and _application_traceback, which contain the wrapped
    type and value describing the exception, and a chained list of
    PyTraceback objects making the application-level traceback.
    """

    _w_value = None
    _application_traceback = None
    w_cause = None

    def __init__(self, w_type, w_value, tb=None, w_cause=None):
        self.setup(w_type, w_value)
        self._application_traceback = tb
        self.w_cause = w_cause

    def setup(self, w_type, w_value=None):
        assert w_type is not None
        self.w_type = w_type
        self._w_value = w_value
        if not we_are_translated():
            self.debug_excs = []

    def clear(self, space):
        # XXX remove this method.  The point is that we cannot always
        # hack at 'self' to clear w_type and _w_value, because in some
        # corner cases the OperationError will be used again: see
        # test_interpreter.py:test_with_statement_and_sys_clear.
        pass

    def match(self, space, w_check_class):
        "Check if this application-level exception matches 'w_check_class'."
        return space.exception_match(self.w_type, w_check_class)

    def async(self, space):
        "Check if this is an exception that should better not be caught."
        return (self.match(space, space.w_SystemExit) or
                self.match(space, space.w_KeyboardInterrupt))

    def __str__(self):
        "NOT_RPYTHON: Convenience for tracebacks."
        s = self._w_value
        if self.__class__ is not OperationError and s is None:
            space = getattr(self.w_type, 'space')
            if space is not None:
                s = self._compute_value(space)
        return '[%s: %s]' % (self.w_type, s)

    def __repr__(self):
        "NOT_RPYTHON"
        return 'OperationError(%s)' % (self.w_type)

    def errorstr(self, space, use_repr=False):
        "The exception class and value, as a string."
        w_value = self.get_w_value(space)
        if space is None:
            # this part NOT_RPYTHON
            exc_typename = str(self.w_type)
            exc_value = str(w_value)
        else:
            w = space.wrap
            if space.is_w(space.type(self.w_type), space.w_text):
                exc_typename = space.str_w(self.w_type)
            else:
                exc_typename = space.str_w(
                    space.getattr(self.w_type, w('__name__')))
            if space.is_w(w_value, space.w_None):
                exc_value = ""
            else:
                try:
                    if use_repr:
                        exc_value = space.str_w(space.repr(w_value))
                    else:
                        exc_value = space.str_w(space.str(w_value))
                except OperationError:
                    # oups, cannot __str__ the exception object
                    exc_value = "<oups, exception object itself cannot be str'd>"
        if not exc_value:
            return exc_typename
        else:
            return '%s: %s' % (exc_typename, exc_value)

    def record_interpreter_traceback(self):
        """Records the current traceback inside the interpreter.
        This traceback is only useful to debug the interpreter, not the
        application."""
        if not we_are_translated():
            if RECORD_INTERPLEVEL_TRACEBACK:
                self.debug_excs.append(sys.exc_info())

    def print_application_traceback(self, space, file=None):
        "NOT_RPYTHON: Dump a standard application-level traceback."
        if file is None:
            file = sys.stderr
        self.print_app_tb_only(file)
        print >> file, self.errorstr(space)

    def print_app_tb_only(self, file):
        "NOT_RPYTHON"
        tb = self._application_traceback
        if tb:
            import linecache
            print >> file, "Traceback (application-level):"
            while tb is not None:
                co = tb.frame.pycode
                lineno = tb.get_lineno()
                fname = co.co_filename
                if fname.startswith('<inline>\n'):
                    lines = fname.split('\n')
                    fname = lines[0].strip()
                    try:
                        l = lines[lineno]
                    except IndexError:
                        l = ''
                else:
                    l = linecache.getline(fname, lineno)
                print >> file, "  File \"%s\"," % fname,
                print >> file, "line", lineno, "in", co.co_name
                if l:
                    if l.endswith('\n'):
                        l = l[:-1]
                    l = "    " + l.lstrip()
                    print >> file, l
                tb = tb.next

    def print_detailed_traceback(self, space=None, file=None):
        """NOT_RPYTHON: Dump a nice detailed interpreter- and
        application-level traceback, useful to debug the interpreter."""
        if file is None:
            file = sys.stderr
        f = io.StringIO()
        for i in range(len(self.debug_excs)-1, -1, -1):
            print >> f, "Traceback (interpreter-level):"
            traceback.print_tb(self.debug_excs[i][2], file=f)
        f.seek(0)
        debug_print(''.join(['|| ' + line for line in f.readlines()]), file)
        if self.debug_excs:
            from pypy.tool import tb_server
            tb_server.publish_exc(self.debug_excs[-1])
        self.print_app_tb_only(file)
        print >> file, '(application-level)', self.errorstr(space)
        if AUTO_DEBUG:
            debug.fire(self)

    def normalize_exception(self, space):
        """Normalize the OperationError.  In other words, fix w_type and/or
        w_value to make sure that the __class__ of w_value is exactly w_type.
        """
        #
        # This method covers all ways in which the Python statement
        # "raise X, Y" can produce a valid exception type and instance.
        #
        # In the following table, 'Class' means a subclass of BaseException
        # and 'inst' is an instance of either 'Class' or a subclass of it.
        #
        # The flow object space only deals with non-advanced case.
        #
        #  input (w_type, w_value)... becomes...                advanced case?
        # ---------------------------------------------------------------------
        #  (Class, None)              (Class, Class())                no
        #  (Class, inst)              (inst.__class__, inst)          no
        #  (Class, tuple)             (Class, Class(*tuple))          yes
        #  (Class, x)                 (Class, Class(x))               no
        #  (inst, None)               (inst.__class__, inst)          no
        #
        w_type = self.w_type
        w_value = self.get_w_value(space)

        if space.exception_is_valid_obj_as_class_w(w_type):
            # this is for all cases of the form (Class, something)
            if space.is_w(w_value, space.w_None):
                # raise Type: we assume we have to instantiate Type
                w_value = space.call_function(w_type)
                w_type = self._exception_getclass(space, w_value)
            else:
                w_valuetype = space.exception_getclass(w_value)
                if space.exception_issubclass_w(w_valuetype, w_type):
                    # raise Type, Instance: let etype be the exact type of value
                    w_type = w_valuetype
                else:
                    if space.isinstance_w(w_value, space.w_tuple):
                        # raise Type, tuple: assume the tuple contains the
                        #                    constructor args
                        w_value = space.call(w_type, w_value)
                    else:
                        # raise Type, X: assume X is the constructor argument
                        w_value = space.call_function(w_type, w_value)
                    w_type = self._exception_getclass(space, w_value)
            if self.w_cause:
                # ensure w_cause is of a valid type
                if space.is_none(self.w_cause):
                    pass
                else:
                    self._exception_getclass(space, self.w_cause, "exception causes")
                space.setattr(w_value, space.wrap("__cause__"), self.w_cause)
            if self._application_traceback:
                from pypy.interpreter.pytraceback import PyTraceback
                from pypy.module.exceptions.interp_exceptions import W_BaseException
                tb = self._application_traceback
                if (isinstance(w_value, W_BaseException) and
                    isinstance(tb, PyTraceback)):
                    # traceback hasn't escaped yet
                    w_value.w_traceback = tb
                else:
                    # traceback has escaped
                    space.setattr(w_value, space.wrap("__traceback__"),
                                  space.wrap(self.get_traceback()))
        else:
            # the only case left here is (inst, None), from a 'raise inst'.
            w_inst = w_type
            w_instclass = self._exception_getclass(space, w_inst)
            if not space.is_w(w_value, space.w_None):
                raise OperationError(space.w_TypeError,
                                     space.wrap("instance exception may not "
                                                "have a separate value"))
            w_value = w_inst
            w_type = w_instclass

        self.w_type = w_type
        self._w_value = w_value

    def _exception_getclass(self, space, w_inst, what="exceptions"):
        w_type = space.exception_getclass(w_inst)
        if not space.exception_is_valid_class_w(w_type):
            raise oefmt(space.w_TypeError,
                        "%s must derive from BaseException, not %N",
                        what, w_type)
        return w_type

    def write_unraisable(self, space, where, w_object=None,
                         with_traceback=False, extra_line=''):
        if w_object is None:
            objrepr = ''
        else:
            try:
                objrepr = space.str_w(space.repr(w_object))
            except OperationError:
                objrepr = '?'
        #
        try:
            if with_traceback:
                try:
                    self.normalize_exception(space)
                except OperationError:
                    pass
                w_t = self.w_type
                w_v = self.get_w_value(space)
                w_tb = space.wrap(self.get_traceback())
                space.appexec([space.wrap(where),
                               space.wrap(objrepr),
                               space.wrap(extra_line),
                               w_t, w_v, w_tb],
                """(where, objrepr, extra_line, t, v, tb):
                    import sys, traceback
                    if where or objrepr:
                        sys.stderr.write('From %s%s:\\n' % (where, objrepr))
                    if extra_line:
                        sys.stderr.write(extra_line)
                    traceback.print_exception(t, v, tb)
                """)
            else:
                msg = 'Exception %s in %s%s ignored\n' % (
                    self.errorstr(space, use_repr=True), where, objrepr)
                space.call_method(space.sys.get('stderr'), 'write',
                                  space.wrap(msg))
        except OperationError:
            pass   # ignored

    def get_w_value(self, space):
        w_value = self._w_value
        if w_value is None:
            value = self._compute_value(space)
            self._w_value = w_value = space.wrap(value)
        return w_value

    def _compute_value(self, space):
        raise NotImplementedError

    def get_traceback(self):
        """Calling this marks the PyTraceback as escaped, i.e. it becomes
        accessible and inspectable by app-level Python code.  For the JIT.
        Note that this has no effect if there are already several traceback
        frames recorded, because in this case they are already marked as
        escaping by executioncontext.leave() being called with
        got_exception=True.
        """
        from pypy.interpreter.pytraceback import PyTraceback
        tb = self._application_traceback
        if tb is not None and isinstance(tb, PyTraceback):
            tb.frame.mark_as_escaped()
        return tb

    def set_traceback(self, traceback):
        """Set the current traceback.  It should either be a traceback
        pointing to some already-escaped frame, or a traceback for the
        current frame.  To support the latter case we do not mark the
        frame as escaped.  The idea is that it will be marked as escaping
        only if the exception really propagates out of this frame, by
        executioncontext.leave() being called with got_exception=True.
        """
        self._application_traceback = traceback

    def remove_traceback_module_frames(self, module_name):
        from pypy.interpreter.pytraceback import PyTraceback
        tb = self._application_traceback
        while tb is not None and isinstance(tb, PyTraceback):
            if tb.frame.pycode.co_filename != module_name:
                break
            tb = tb.next
        self._application_traceback = tb

    def record_context(self, space, frame):
        """Record a __context__ for this exception from the current
        frame if one exists.

        __context__ is otherwise lazily determined from the
        traceback. However the current frame.last_exception must be
        checked for a __context__ before this OperationError overwrites
        it (making the previous last_exception unavailable later on).
        """
        last_exception = frame.last_exception
        if (last_exception is not None and not frame.hide() or
            last_exception is get_cleared_operation_error(space)):
            # normalize w_value so setup_context can check for cycles
            self.normalize_exception(space)
            w_value = self.get_w_value(space)
            w_last = last_exception.get_w_value(space)
            w_context = setup_context(space, w_value, w_last, lazy=True)
            space.setattr(w_value, space.wrap('__context__'), w_context)


def oefmt(w_type, valuefmt, *args):
    """Equivalent to OperationError(w_type, space.wrap(valuefmt % args)).
    More efficient in the (common) case where the value is not actually
    needed. Note that in the py3k branch the exception message will
    always be unicode.

    Supports the standard %s and %d formats, plus the following:

    %8 - The result of arg.decode('utf-8')
    %N - The result of w_arg.getname(space)
    %R - The result of space.unicode_w(space.repr(w_arg))
    %T - The result of space.type(w_arg).name

    """
    if not len(args):
        return OpErrFmtNoArgs(w_type, valuefmt)
    OpErrFmt, strings = get_operr_class(valuefmt)
    return OpErrFmt(w_type, strings, *args)
