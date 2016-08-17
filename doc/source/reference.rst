Reference
=========

Special variables
-----------------

There are a set of special variables in ``ayrton``. Most of them are inherited
from shell like languages.

.. py:data:: argv

    This variable holds a list of the arguments passed to the script, with the
    script's path in the first position. In Python-speak, this is ``sys.argv``.

    It's not quite a list: `len(argv)`, `iter(argv)` and `argv.pop()` don't
    take in account `argv[0]`.

.. py:data:: path

    This variable holds a list of strings, each one representing a directory.
    When binaries are executed (see :py:func:`foo`), they're searched in these
    directories by appending *foo* to each one of the directories until an
    executable is found.

Exceptions
----------

.. py:exception:: CommandNotFound

    Raised when an executable cannot be found in :py:data:`path`. Unluckily,
    currently it is raised sometimes you refer to an unknow variable too. We're
    working to minimize that, but there might be still more cases were it does so.

.. py:exception:: CommandFailed

    Raised when the `errexit` :py:func:`option` is set and a command exits with
    a code that is not 0.

Functions
---------

.. :py:function:: bash (list_or_str)

    Apply ``bash``'s brace, tilde and pathname (also called glob) expansions (in
    that order). *list_or_str* can be a string or a list of strings. The return
    value can be an empty list, a single string, or a list of two or more strings.

.. py:function:: cd (path) | chdir (path)

    Changes the current working directory for the script process. If used as a
    context manager, it restores the original path when the context finishes,
    efectively working more or less like `pushd`/`popd` or `( cd path; ... )`.

.. py:function:: export (key=value, ...)

    For each *key* and *value* pair, set the variable *key* to the string
    representation of *value*, and register the variable as to be exported to
    subproceses.

.. py:function:: o (name=value)

    Creates a positional option that will be expanded as an option/value when
    running a command. See :py:func:`foo`. This is mostly used internally.

.. py:function:: option (opt, value=True)

    Works more or less like `bash`'s `set` builtin command. *opt* can be in its
    long form, in which case you can pass the new *value*, or in the set/unset
    short form. So far only the following options are recognized:

    `errexit`/`-e`/`+e`
      If set, any command that exits with a code which is not 0 will raise a
      :py:exc:`CommandFailed` exception.

    It raises a ValueError if the option is malformed, and KeyError if the option
    is not recognized.

.. py:function:: remote (..., )

    This function is better used as a context manager::

        with remote ():
            ...

    The function accepts the same arguments as ``paramiko``'s
    `SSHClient.connect() <http://docs.paramiko.org/paramiko.SSHClient-class.html#connect)>`_
    method. The body of the construct is executed in the remote machine.

    For the moment imports are weeded out from the remote environment, so you
    will need to reimport them.

.. py:function:: run (rel_or_abs_path, [*args, [**kwargs]])

    Executes an arbitrary binary that is not in :py:data:`path`. *rel_or_abs_path*
    must be a relative or absolute path.

.. py:function:: shift (n=1)

    Pops the first *n* elements from :py:data:`argv` and return them. If *n* is
    1, the value returned is just the first element; if it's bigger than 1, it
    returns a list with those *n* elements.

.. py:function:: unset (*args)

    For each variable name in *\*args*, unset the variable and remove it from
    the environment to be exported to subprocesses. Notice that it must be a list
    of strings, not the variables themselves. Unknown variables will be silently
    ignored.

.. py:function:: foo (...)

    Executes the binary *foo*, searching the binary using :py:data:`path`.
    Arguments are used as positional arguments for the command, except for the
    special keyword arguments listed below. This
    returns a :py:class:`Command`.

    The syntaxis for Commands departs a little from
    pure Python. Python expressions are allowed as keyword names, so `-o` and
    `--long-option` are valid. Also, keywords and positional arguments can be mixed,
    as in `find (-L=True, '/', -name='*.so')`.

    Iterable arguments that are not
    :py:class:`str` or :py:class:`bytes` are expanded in situ, so `foo(..., i, ...)`
    is expanded to `foo (..., i[0], i[1], ...` and `foo(..., k=i, ...)` is expanded
    to `foo (..., k=i[0], k=i[1], ...`.

.. py:attribute:: _in

    Establishes what or where does the contents of *stdin* come from, depending
    on its value or type:

        * If it's `None`, it's connected to `/dev/null`.
        * If it's a file object [#file_objects]_, it uses its contents.
        * If its type is ``int``, it's considered a file descriptor from where
          the input is read.
        * If its type is ``str`` or ``bytes``, it's considered the name of the file
          from where the input is read.
        * if it's an iterable, then it's the `str()` of each elements.
        * Else, it's the `str()` of it.

.. py:attribute:: _out

    Defines where the *stdout* goes to, depending on its value or type:

        * If it's `None`, it goes to `/dev/null`.
        * If it's `Capture`, the output is read by the object.
        * If it's a file object [#file_objects]_, the output is written on it.
        * If its type is ``int``, it's considered a file descriptor to where
          the output is written.
        * It its type is ``str`` or ``bytes``, it's the filename where the output
          goes.
        *

.. [#file_objects] For the moment it only includes ``io.IOBase`` instances and
    its ``fileno()`` is used; this does not include objects that duck-type a file.

.. [#undecided] This is inconsistent on what happens in :py:attr:`_out` and
    :py:attr:`_err`. This might be deprecated in the future.

Special types
-------------

.. py:class:: Command


Tests
-----

The following functions are based on ``bash``'s `tests for file attributes
<https://www.gnu.org/software/bash/manual/html_node/Bash-Conditional-Expressions.html#Bash-Conditional-Expressions>`_.
For string and arithmetic operations and comparison use Python's ``int`` and
``str`` methods.

Note: *_t*, *_G*, *_O* and *_ef* are not implemented yet.

.. py:function:: _a (file)

    True if *file* exists.

.. py:function:: _b (file)

    True if *file* is a block device.

.. py:function:: _c (file)

    True if *file* is a char device.

.. py:function:: _d (file)

    True if *file* is a directory.

.. py:function:: _e (file)

    See :py:func:`_a`.

.. py:function:: _f (file)

    True if *file* is a regular file.

.. py:function:: _g (file)

    True if *file*'s *setgid* bit is on.

.. py:function:: _h (file)

    True if *file*' is a symlink.

.. py:function:: _k (file)

    True if *file*'s *sticky* bit is on.

.. py:function:: _p (file)

    True if *file* is a FIFO/named pipe.

.. py:function:: _r (file)

    True if *file* is readable.

.. py:function:: _s (file)

    True if *file*'s size is >0.

.. py:function:: _u (file)

    True if *file*'s *setuid* attribute is on.

.. py:function:: _w (file)

    True if *file* is writable.

.. py:function:: _x (file)

    True if *file* is executable.

.. py:function:: _x (file)

    See :py:func:`_h`.

.. py:function:: _N (file)

    True if *file*'s modification time (*mtime*) is newer than its access time
    (*atime*).

.. py:function:: _S (file)

    True if *file* is a socket.

.. py:function:: _nt (file1, file2)

    True if *file1* exists and *file2* does not, or if *file1*'s *mtime* is newer
    than *file2*'s.

.. py:function:: _ot (file1, file2)

    True if *file2* exists and *file1* does not, or if *file1*'s *mtime* is older
    than *file2*'s.


Python functions
----------------

Some Python functions from the standard library are available as global functions
in ``ayrton``, some of them under a different, more shell-like name. Notice that
these function most probably hide an executable of the same name.

.. py:function:: exit ([exit_code])

    Finish the script with an exit code equal to *exit_code*. By default it's 0.
    For more details, see http://docs.python.org/3/library/sys.html#sys.exit .

.. py:function:: pwd ()

    Returns the process' current working directory. For more details, see
    For more details, see http://docs.python.org/3/library/os.html#os.getcwd .

.. py:function:: sleep ()

    Suspend execution for the given number of seconds. The argument may be a
    floating point number to indicate a more precise sleep time. For more details,
    see http://docs.python.org/3/library/time.html#time.sleep

.. py:function:: uname ()

    For more details, see http://docs.python.org/3/library/os.html#os.uname .

More functions might be already exported as builtins, but are not yet documented.
Please check ``ayton/__init__.py``'s ``polute()`` function for more details.

There are some Python functions that would seem to also make sense to include here.
Most of them are C-based functions that have the same name as a more powerful
executable, like ``chmod``, ``mkdir``, etc. If you think we oversaw an useful
function, drop us a line.
