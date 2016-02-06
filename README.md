`ayrton` - a shell-like scripting language strongly based on Python3.

`ayrton` is an modification of the Python language that tries to make it look more
like a shell programming language. It takes ideas already present in `sh`, adds
a few functions for better emulating envvars, and provides a mechanism for (semi)
transparent remote execution via `ssh`.

`ayrton` syntax is Python3's with some things changed. Here's the unavoidable
'Hello world' example:

    print ('Hello, World!')

Nothing fancy, right? Let's try something slightly different:

    echo ('Hello, World!')

Not interested yet? What if I tell you that `echo` function just
executed `/bin/echo`?:

    mdione@diablo:~/src/projects/ayrton$ strace -e process -ff ayrton doc/examples/hw.ay
    execve("/home/mdione/local/bin/ayrton", ["ayrton", "doc/examples/hw.ay"], [/* 40 vars */]) = 0
    [...]
    [pid   404] execve("/bin/echo", ["/bin/echo", "Hello, World!"], [/* 40 vars */]) = 0

This code is released under the [GPLv3](http://www.gnu.org/licenses/gpl-3.0.html).
If you're unsure on how this apply to your interpreted programs, check
[this entry in their FAQ](https://www.gnu.org/licenses/gpl-faq.html#IfInterpreterIsGPL).

Currently `ayrton` is under heavy development, so if you're following it and
clone it, use the branch `develop`.

# Installation

`ayrton` depends on two pieces of code. Python is the most obvious; it has been
developed in its version 3.3. Python 3.2 is not enough, sorry. On the other hand,
as Python3 has not completely caught yet, most probably even less
in stable server environments, in the future we plan to support at least Python2.7.

The second dependency is [`paramiko`](https://github.com/paramiko/paramiko).

So, in short:

    # apt-get install python3-paramiko # this also brings deps and python3 :)

    # git clone https://github.com/StyXman/ayrton.git
    # cd ayrton
    # make tests
    # python3 setup.py install
    or edit Makefile and
    # make install

    To generate the docs:
    # make docs

# First steps: execution, output

To do the same as the second example in the introduction,
with `sh` you could `from sh import echo` and it will create a callable that will
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

# Composing

Just like `sh`, you can nest callables:

    root= grep (cat ('/etc/passwd'), 'root', _out=Capture)

In the special case where a command is the first argument for another, its output
will be captured and piped to the stdin of the outer command.

Another improvement over `sh` is that you can use commands as conditions:

    if grep (cat ('/etc/passwd'), 'mdione', _out=None):
        print ('user «mdione» is present on your system; that's a security vulnerability right there!')

As a consequence, you can also use `and`, `or` and `not`.

# Piping, redirection

Of course, no shell scripting language can call itself so without piping, so
we had to implement it:

    if cat ('/etc/passwd') | grep ('mdione', _out=None):
        print ('I'm here, baby!')

And of course, we also have redirection:

    grep ('mdione') < '/etc/passwd' > '/tmp/foo'
    grep ('root') < '/etc/passwd' >> '/tmp/foo'

# Shell compatibility

Do I have you attention? Let's go for your interest. Something also useful is a
behavior similar to `pushd`/`popd`:

    with cd ('bin'):
        print (pwd ()) # prints $PWD/bin
    print (pwd ())     # prints $PWD

If you were in `ayrton`'s source directory, you would get something in the lines
of:

    /home/mdione/src/projects/ayrton/bin
    /home/mdione/src/projects/ayrton

The `bash()` function applies brace, tilde and glob (pathname) expansions:

    >>> from ayrton.expansion import bash
    >>> import os
    >>> os.chdir (bash ('~/src/pro*/osm/mapn*')[0])
    >>> os.getcwd ()
    '/home/mdione/src/projects/osm/mapnik-stylesheets'
    >>> bash ("Elevation/{legend*,Elevation.dgml,preview.png,Makefile}")
    ['Elevation/legend.html', 'Elevation/legend', 'Elevation/Elevation.dgml', 'Elevation/preview.png', 'Elevation/Makefile']

Notice that `bash()` always returns a list, which might be empty or has one or more elements.

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

# Remote execution

The cherry on top of the cake, or more like the melon of top of the cupcake, is
(semi) transparent remote execution. This is achieved with the following construct:

    a= 42
    with remote ('localhost'):
        # we can also access variables already in the scope
        # even when we're actually running in another machine
        print (a)
        # we can modify those variables
        a= 27

    # and those modifications are reflected locally
    assert (a, 27)

The body of the `with remote(): ...` statement is actually executed in a remote
machine after connecting via `ssh`. The `remote()` context manager accepts the
same parameters as `paramiko`'s
[`SSHClient.connect()`](http://docs.paramiko.org/paramiko.SSHClient-class.html#connect)
method.

The implementation of this construct limits a bit what can be done in its body.
The code is converted into a AST subtree and the local environment is pickled.
If the latter fails the construct fails and your script will finish. We're
checking its limitations to see where we can draw the line of what will be
possible or not.

The development of this construct is not complete, so expect some changes in its
API.

Here you'll find [the docs](http://www.grulic.org.ar/~mdione/projects/ayrton/).

# FAQ

Q: Why bother? Isn't `bash` great?

A: Yes and no. `bash` is very powerful, both from the CLI point of view and as a language.
But it's clumsy, mainly due to two reasons: parsing lines into commands and their
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

Q: Instead, why not use...

A: (Short version) We think nobody provides all of `ayrton`'s features.

A: ... [`sh`](https://amoffat.github.io/sh/)? Well, we started with `sh` as a basis
of `ayrton`, but its buffered output didn't allow us to run editors and other TIU's.

A: ... [`xonsh`](http://xonsh.org/)? `xonsh` keeps environment variables in a different
namespace than the Python ones; it even has a Python mode and a 'subprocess' mode
(although lots of Python characteristics can be used in the subprocess mode and vice versa);
and is more oriented to being a shell. `ayrton` aims directly in the opposite
direction.

A: ... [`plumbum`](https://plumbum.readthedocs.org/en/latest/)? You could say that we
independently thought of its piping and redirection syntax (but in reality we just
based ours on `bash`'s). Still, the fact that you first build pipes and then execute
them looks weird for a SysAdmin.

A: ... [`fabric`](http://www.fabfile.org/)? `fabric` is the only one that has remote
execution and the `cd` context manager, but command execution is still done via
strings.

# Thanks to:

`rbilstolfi`, `marianoguerra`, `facundobatista`, `ralsina` for ideas; `nessita` for unit
testing support; `Darni` for pointing me to
[nvie's workflow for `git`](http://nvie.com/posts/a-successful-git-branching-model/),
Andrew Moffat for [`sh`](http://amoffat.github.io/sh/) and Richard Jones for
this talk (thanks again, `ralsina`), even when I ended up doing something
different:

[Don't do this](http://www.youtube.com/watch?feature=player_embedded&v=H2yfXnUb1S4)

# Things to come

See TODO.rst
