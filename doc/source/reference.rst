Reference
=========

Special variables
-----------------

There are a set of special variables in ``ayrton``. Most of them are inherited
from shell like languages.

.. py:data:: argv

    This variable holds a list of the arguments passed to the script, with the
    script's path in the first position.

.. py:data:: path

    This variable holds a list of strings, each one representing a directory.
    When binaries are executed (see :py:func:``foo``), they're searched in these
    directories by appending *foo* to each of the directory until an executable
    is found.

Exceptions
----------

.. py:exception:: CommandNotFound

    Raised when an executable cannot be found in :py:data:``path``. Unluckily,
    currently is raised everytime you refer to an unknow variable too.

Functions
---------

.. :py:function:: bash (list_or_str)

    Apply ``bash``'s brace, tilde and pathname (also called glob) expansions (in
    that order). *list_or_str* can be a string or a list of strings. The return
    value is always a list of strings.

.. py:function:: cd (path)

    Changes the current working directory for the script process. If used as a
    context manager, it restores the original path.

.. py:function:: export (key=value, ...)

    For each *key* and *value* pair, set the variable *key* to the string
    representation of *value*, and register the variable as to be exported to
    subproceses.

.. py:function:: run (rel_or_abs_path, [*args, [**kwargs]])

    Executes an arbitrary binary that is not in :py:data:``path``. *rel_or_abs_path*
    must be a relative or absolute path.

.. py:function:: unset (*args)

    For each variable name in *\*args*, unset the variable and remove it from
    the environment to be exported to subproceses. Notice that it must be a list
    of strings, not the variables themselves. Unknow variables will be silently
    ignored.

.. py:function:: foo ([*args, [**kwars]])

    Executes the binary *foo*, searching the binary using :py:data:``path``.

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

More function might be aready exported as builtins, but are not yet documented.
Please check ``ayton/__init__.py``'s ``polute()`` functions for more details.

There are some Python function that would seem to also make sense to include here.
Most of them are C-based functions that have the same name as a more powerful
executable, like ``chmod``, ``mkdir``, etc. If you whink we oversaw an useful
function,  drop us a line.
