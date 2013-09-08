ayrton - a shell like language with the power of python.

ayrton is an extension of the Python language that tries to make it look more
like a shell programming language. It takes ideas already present in `sh`, adds
a few functions for better emulating envvars, and provides a mechanism for (semi)
transparent remote execution via `ssh`.

This code is released under the [GPLv3](http://www.gnu.org/licenses/gpl-3.0.html).
If you're unsure on how this apply to your interpreted programs, check
[this entry in their FAQ](https://www.gnu.org/licenses/gpl-faq.html#IfInterpreterIsGPL).

Currently `ayrton` is under heavy development, so if you're following it and
clone it (there are no releases yet), use the branch `develop`.

# Instalation

`ayrton` depends on three pieces of code. Python is the most obvious; it has been
developed in its version 3.3. Next is [`sh`](http://amoffat.github.io/sh/), version
1.08. The last item is more complicated. It uses
[`paramiko`](https://github.com/paramiko/paramiko), but as this project tries to
be compatible with lower versions of Python2, there's no official port for Python3.
We used an [unofficial port](http://github.com/nischu7/paramiko) that works pretty
well so far. As Python3 has not completely caught yet, most probably even less
in stable server environments, we plan to support at least Python2.7.

So, in short:

    # apt-get install python3

    # git clone https://github.com/amoffat/sh.git
    # cd sh
    # python3 setup.py install
    # cd ..

    # git clone https://github.com/nischu7/paramiko.git
    # cd paramiko
    # python3 setup.py install
    # cd ..

    # git clone https://github.com/StyXman/ayrton.git
    # cd ayrton
    # make tests
    # python3 setup.py install
    or edit Makefile and
    # make install

    To generate the docs:
    # make docs

# First steps

`ayrton` syntax is Python3's with some things changed. Here's the unavoidable
'Hello world' example:

    print ('Hello, World!')

Nothing fancy, right? Let's try something slightly different:

    echo ('Hello, World!')

Not interested yet? What if I tell you that that `echo` function just
executed `/bin/echo`?:

    mdione@diablo:~/src/projects/ayrton$ strace -e process -ff ayrton doc/examples/hw.ay
    execve("/home/mdione/local/bin/ayrton", ["ayrton", "doc/examples/hw.ay"], [/* 40 vars */]) = 0
    [...]
    [pid   404] execve("/bin/echo", ["/bin/echo", "Hello, World!"], [/* 40 vars */]) = 0

With `sh` you could `from sh import echo` and it will create a callable that will
transparently run `/bin/echo` for you; `ayrton` takes a step further and creates
the callable on the fly, so you don't have to pre-declare it. Another difference
is that under `sh`, `echo`'s output gets captured by default, which means that
you don't see it unless you later print it. `ayrton` tries to be more shell-like,
sending the output where it should. If you want to capture the output, just tell
it so:

    hw= echo ('Hello, World!', _out=Capture)

While we're discussing output, check out this:

    echo ('Hello, World!', _out=None)

Just guess were the output went :) ... (ok, ok, it went to `/dev/null`).

Just like `sh`, you can nest callables, but you must explicitly tell it that you
want to capture the output so the nesting callable gets its input:

    root= grep (cat ('/etc/shadow', _out=Capture), 'root', _out=Capture)

This seems more cumbersome than `sh`, but if you think that in any shell language
you do something similar (either using `$()`, `|` or even redirection), it's not
a high price to pay.

Another improvement over `sh` is that you can use commands as conditions:

    if grep (cat ('/etc/shadow', _out=Capture), 'mdione', _out=None):
        print ('user «mdione» is present on your system; that's a security vulnerability right there!')

As a consequence, you can also use `and`, `or` and `not`.

Do I have you attention? Let's go for your interest. Something also useful is a
behavior similar to `pushd`/`popd`:

    with cd ('bin'):
        print (pwd ())
    print (pwd ())

If you were in `ayrton`'s source directory, you would get something in the lines
of:

    /home/mdione/src/projects/ayrton/bin
    /home/mdione/src/projects/ayrton

`bash()` applies brace, tilde and glob (pathname) expansions:

    >>> from ayrton.expansion import bash
    >>> import os
    >>> os.chdir (bash ('~/src/pro*/osm/mapn*')[0])
    >>> os.getcwd ()
    '/home/mdione/src/projects/osm/mapnik-stylesheets'
    >>> bash ("Elevation/{legend*,Elevation.dgml,preview.png,Makefile}")
    ['Elevation/legend.html', 'Elevation/legend', 'Elevation/Elevation.dgml', 'Elevation/preview.png', 'Elevation/Makefile']

Notice that `bash()` always returns a list.

Parameter expansion can be achieved with the `str` operator `%` or the `format()`
method. Arithmetic expansion can be achieved with normal arithmetic operators.
Process substitution is planned but not yet implemented.

There is no need for a `test`/`[`/`[[` equivalent, but there are for the
operators. As `-`cannot be part of the name of a function, we replaced it with `_`.
So, `-f` became `_f()` and so on. Some of the operators are not implemented yet.
Of course, string and integer operators are better implemented in Python's `str`,
`int` and, why not, `float` types.

One main difference between Python and shell languages is that in the latter, you only have
environment variables, which after being exported, can be seen by any subprocess.
In Python there are two worlds: Python variables and environment variables.
`ayrton` again reaches to shell languages, mixing the environment into the globals,
so envvars can be reached from any place, just like in shell scripts. Notice that
new variables in `ayrton` (f.i., `foo=42`) are Python variables; therefore they
can hold any Python object, but won't be exported. The `export()` function
gives the same behavior as `bash`'s `export` command, with the caveat that values
will be automatically converted to `str`.

The cherry on top of the cake, or more like the melon of top of the cupcake, is
(semi) transparent remote execution. This is achieved with the following construct:

    a= 42
    with ssh ('localhost') as streams:
        foo= input ()
        print (foo)
        # we can also access variables already in the scope
        # even when we're actually running in another machine
        print (a)

    # streams returns 3 streams: stdin, stdout, stderr
    (i, o, e)= streams
    # notice that we must include the \n at the end so input() finishes
    # and that you must transmit bytes only, no strings
    i.write (b'bar\n')
    print (o.readlines ())


The body of the `with ssh(): ...` statement is actually executed in a remote
machine after connecting via `ssh`. The `ssh()` context manager accepts the
same parameters as `paramiko`'s
[`SSHClient.connect()`](http://docs.paramiko.org/paramiko.SSHClient-class.html#connect)
method.

The implementation of this construct limits a bit what can be done in its body.
The code is converted into a AST subtree and the local environment is pickled.
If the latter fails the construct fails and your script will finish. We're
checking its limitations to see where we can draw the line of what will be
possible or not.

# FAQ

Q: Why bother? Isn't `bash` great?

A: Yes and no. `bash` is very powerful, both from the CLI and as a language. But
it's clumsy, mainly due to two reasons: parsing lines into commands and their
arguments, and the methods for preventing overzealous word splitting, which leads
to several pitfalls, some of them listed [here](http://mywiki.wooledge.org/BashPitfalls));
and poor data manipulation syntax.  It also lacks of good remote
execution support. Most scripts start small, but once they reach
a certain size/complexity, either they become monsters (resembling a Frankenstein
built using a Kafkian method) or they are rewritten in Perl (which makes them a
different kind of monster, closer to the Thing in «The Thing»).

Q: Why not contribute all this to `sh`?

A: `sh` has a very specific objective, which is to make easy to capture the
output of commands into a Python script, and even pipe output to other commands
in a functional/pythonic way. `ayrton` aims to make python+sh behave more like
`bash` so it's easier for sysadmins to learn and use. Anything that still holds
`sh`'s objective will be sent as a patch over time, but for the moment being,
we're still playing with the shape of `ayrton`.

Q: `ayrton` is too verbose! I don't want to put extra `()`'s or `'`'s everywhere.

A: Shell languages have evolved from shell interpreters. Command execution are
their main objective, and its syntax is designed around it. That leads to
shortcuts that later are more difficult to read and creates problems when
handling filenames that have special characters.

# Thanks to:

`rbilstolfi`, `marianoguerra`, `facundobatista`, `ralsina`, `nessita` for unit
testing support, `Darni` for pointing me to
[nvie's workflow for `git`](http://nvie.com/posts/a-successful-git-branching-model/),
Andrew Moffat for [`sh`](http://amoffat.github.io/sh/) and Richard Jones for
this talk (thanks again, `ralsina`), even when I ended up doing something
different:

[Don't do this](http://www.youtube.com/watch?feature=player_embedded&v=H2yfXnUb1S4)

# Things to come

See TODO.rst
