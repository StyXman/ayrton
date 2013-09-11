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
    When binaries are executed (see :py:func:`foo`), they're searched in these
    directories by appending *foo* to each of the directory until an executable
    is found.

Exceptions
----------

.. py:exception:: CommandNotFound

    Raised when an executable cannot be found in :py:data:`path`. Unluckily,
    currently is raised everytime you refer to an unknow variable too.

Functions
---------

.. :py:function:: bash (list_or_str)

    Apply ``bash``'s brace, tilde and pathname (also called glob) expansions (in
    that order). *list_or_str* can be a string or a list of strings. The return
    value is always a list of strings.

.. py:function:: cd (path)

    Changes the current working directory for the script process. If used as a
    context manager, it restores the original path when the context finishes,
    efectively working more or less like `pushd`/`popd` or `( cd path; ... )`.

.. py:function:: export (key=value, ...)

    For each *key* and *value* pair, set the variable *key* to the string
    representation of *value*, and register the variable as to be exported to
    subproceses.

.. py:function:: run (rel_or_abs_path, [*args, [**kwargs]])

    Executes an arbitrary binary that is not in :py:data:`path`. *rel_or_abs_path*
    must be a relative or absolute path.

.. py:function:: ssh (..., [_python_only=False])

    This function is better used as a context manager::

        with ssh ():
            ...

    The function accepts the same arguments as ``paramiko``'s
    `SSHClient.connect() <http://docs.paramiko.org/paramiko.SSHClient-class.html#connect)>`_
    method. The body of the construct is executed in the remote machine.

    The function returns 3 streams that represent ``stdin``, ``stdout`` and
    ``sterr``. These streams have ``write()``, ``read(n)``, ``readline()`` and
    ``readlines()`` methods that can be used to interact with the remote. They
    only accept or return ``bytes``, not ``strings``. For more information
    about them, see ``paramiko``'s
    `ChannelFile <https://github.com/nischu7/paramiko/blob/master/paramiko/channel.py#L1233>`_
    (there doesn't seem to be an official doc for this class).

    *_python_only* declares that the body is pure Python code, so we don't try
    to run it under `ayrton`. This allows remotely executing code without needing
    `ayrton` installed in the remote.

    For the moment imports are weeded out from the remote environment, so you
    will need to reimport them.

.. py:function:: unset (*args)

    For each variable name in *\*args*, unset the variable and remove it from
    the environment to be exported to subproceses. Notice that it must be a list
    of strings, not the variables themselves. Unknow variables will be silently
    ignored.

.. py:function:: foo ([*args, [**kwars]])

    Executes the binary *foo*, searching the binary using :py:data:`path`. For
    more information about the parameters, see http://amoffat.github.io/sh/#command-execution
    and http://amoffat.github.io/sh/special_arguments.html#special-arguments .

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

More function might be already exported as builtins, but are not yet documented.
Please check ``ayton/__init__.py``'s ``polute()`` function for more details.

There are some Python function that would seem to also make sense to include here.
Most of them are C-based functions that have the same name as a more powerful
executable, like ``chmod``, ``mkdir``, etc. If you think we oversaw an useful
function,  drop us a line.
