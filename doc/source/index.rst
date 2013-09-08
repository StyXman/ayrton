.. ayrton documentation master file, created by
   sphinx-quickstart on Sun Jul 21 22:47:04 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ayrton's documentation!
==================================

Contents:

.. toctree::
   :maxdepth: 2

   reference


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

Motivation
==========

`ayrton` is an extension of the Python language that tries to make it look more
like a shell programming language. The first thing to note is that it's not
intended to be an interactive shell per se, and I think that anyone used to them for their
day to day computer usage (most notably, fellow SysAdmins) would find such a
shell too cumbersome.

One of the ideas that triggered the development of `ayrton` is that shell
languages have very rudimentary data handling mechanisms: most data are strings;
these strings can be treated as integers in some cinrcumstances; there is no concept
of floats; and a few of them have arrays, even associative ones. For any other
data manipulation, developers have to use tools like `awk`, `sed`, `grep`, `cut`, even
Perl from time to time. In some cases this means that scripts, once they start
to grow a little, become cumbersome and/or unmaintainable.

From the other side, Python is very good at data manipulation, but some things
that are really simple and common in shell languages, like program execution,
are a little more complex in Python. A very good alternative for this is the `sh`
module, but in some aspects it still leaves an alien flavor to a shell
programmer. Here is where `ayrton` comes in and tries to fill in that gap.

`ayrton` is heavily based on the `sh` module, to the point that it even depends on
it. The class responsible for executing commands is just a subclass of
`sh.Command`. For that reason, if you already know ``sh``'s syntax, you can use it.

``ayrton`` for Pythonistas
==========================

As mentioned, `ayrton` is heavily based on the `sh` module, but it introduces
some changes to make it look more like a shell language. This section lists all
the places where it is different from that module and from Python vanilla:

Executables as globals
    The first thing to notice is that you don't need to 'import' the executables
    from ``sh`` (``from sh import ls``) or use them as functions in that module
    (``sh.ls()``).  Instead, you simply invoke the executable as it were a
    global: ``ls()``. **This introduces an unexpected behavior**. This means
    that typos in names will be treated as commands to be run. *This is intentional*.
    This also means that you will get nasty backtraces when the command is not
    found.

*stdout* and *sterr* as default
    In normal scripting languages, commands' output goes directly to the terminal;
    in ``sh`` it goes to the return value of the function. By default, ``ayrton``
    imitates shells scripting. If you want the output to go to the return of the
    function, you have to pass the option ``_out=None``.

Commands do not raise Exceptions
    When you run a command with ``sh`` and it either exited with a return code
    different from 0 or it was stopped/finished by a signal, it would raise an
    exception. You then can recover the exit code and the output from the
    exception. In ``ayrton`` not only exceptions are not raised, you can ask the
    exit code in the ``code`` attribute and the output in the ``stdout`` and
    ``stderr`` attributes. You can also use commands as booleans in conditions
    to ``if``, ``while``, etc: ``if ls(): then echo ("yes!")``.

``ayrton`` for Shell Scripters
==============================

I will not lie to you. This proto-language *will* feel somewhat alien to you.
A lot of things will look like too verbose or explicit, paths now need to be
closed in quotes (``"`` or ``'``), arguments are separated by commas or
sometimes have to be given within a string. We will try to minimize them as much
as possible, but as long as ``ayrton`` uses Python's parser, some will be
impossible to fix. Having said that, we think that ``ayrton`` will be powerful
enough that the benefits will overweight this.

* you don't call ``[``,.
* redirection is done with _out, _err, etc
* currently, absolute and relative paths do not work directly, you have to use run()
* expansions are not done automatilcally; variables can be expanded with %,
  brace, tilde and glob expansions can be done with bash(),
  command substitution is yet to come.
