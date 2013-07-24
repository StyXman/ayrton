.. ayrton documentation master file, created by
   sphinx-quickstart on Sun Jul 21 22:47:04 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ayrton's documentation!
==================================

Contents:

.. toctree::
   :maxdepth: 2



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Motivation
==========

`ayrton` is an extension of the Python language that tries to make it look more
like a shell programming language. The first thing to note is that it's not
intended to be a shell per se, and I think that anyone used to them for their
day to day computer usage (most notably, fellow SysAdmins) would find such a
shell too cumbersome.

One of the ideas that triggered the development of `ayrton` is that shell
languages have very rudimentary data handling mechanisms: most data are strings,
these strings can be treated as integers from time to time, there is no concept
of floats, and a few of them have arrays, even associative ones. For any other
data manipulation, developers have to use tools like `awk`, `sed`, `grep`, `cut`, even
Perl from time to time. In some cases this means that scripts, once they start
to grow a little, become cumbersome and/or unmaintainable.

From the other side, Python is very good for data manipulation, but some things
that are really simple and common in shell languages, like program execution,
are a little more complex in Python. A very good alternative for this is the `sh`
module, but in some aspects it still leaves an alien flavor to a shell
programmer. Here is where `ayrton` comes in and tries to fill in that gap.

`ayrton` is heavily based on the `sh` module, to the point that it even depends on
it. The class responsible for executing commands is just a subclass of
`sh.Command`. For that reason, if you already know sh's syntax, you can use it.
