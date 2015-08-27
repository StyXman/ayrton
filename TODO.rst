Even when most of these are in the github issues, I leave it here so I can
attack it offline (when I code best).

Really do:
----------

* better error reporting, including remotes
* we're weeding out imports, we could gather a list and reimport them in the
  remote

   * from foo import bar is gonna break

* becareful with if cat () | grep (); error codes must be carried too

* process substitution

   * https://github.com/amoffat/sh/issues/66

* enable tracing

   * see pdb's source

* becareful with buitins, might eclipse valid usages: bash() (exp) blocks /bin/bash

   * add option _exec=True for actually executing the binary.

* check ``bash``'s manpage and see what's missing.
* subprocess

   * with ayrton (): ...

* a setting for making references to unkown envvars as in bash.
* trap?

If we {have time,are bored}:
----------------------------

* what to do about relative/absolute command paths?
* executable path caching à la bash.
* git (commit) vs git.commit() vs git ('commit')
* function names are expressions too:
    * / as unary op? => /path/to/excecutable and relative/path
    * foo_bar vs foo__bar vs foo-bar
