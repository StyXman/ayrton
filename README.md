ayrton - a shell like language with the power of python.

Thanks to:

`rbilstolfi`, `marianoguerra`, `facundobatista`, `ralsina`, `nessita` for unit
testing support, `Darni` for pointing me to
[nvie's workflow for `git`](http://nvie.com/posts/a-successful-git-branching-model/),
Andrew Moffat for [`sh`](http://amoffat.github.io/sh/) and Richard Jones for
this talk (thanks again, `ralsina`), even when I ended up doing something
different:

[Don't do this](http://www.youtube.com/watch?feature=player_embedded&v=H2yfXnUb1S4)

This code is released under the [GPLv3](http://www.gnu.org/licenses/gpl-3.0.html).
If you're unsure on how this apply to your interpreted programs, check
[this entry in their FAQ](https://www.gnu.org/licenses/gpl-faq.html#IfInterpreterIsGPL).

Currently `ayrton` is under heavy development, so if you're following it and
clone it (there are no releases yet), use the branch `develop`.

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
the callable on the fly, so you don't have to predeclare it. Another difference
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

We also have expansion à la `bash`, but only the ones that are meaningful, having
in mind that `Python3` already provides the same and even more powerful
functionality:

    touch ('a', 'b.ay')
    files= bash ('{a,b*}')

`bash()` applies brace, tilde and glob expansions:

    >>> from ayrton.expansion import bash
    >>> import os
    >>> os.chdir (bash ('~/src/pro*/osm/mapn*')[0])
    >>> os.getcwd ()
    '/home/mdione/src/projects/osm/mapnik-stylesheets'
    >>> bash ("Elevation/{legend*,Elevation.dgml,preview.png,Makefile}")
    ['Elevation/legend.html', 'Elevation/legend', 'Elevation/Elevation.dgml', 'Elevation/preview.png', 'Elevation/Makefile']

# Things to come

See TODO.rst
