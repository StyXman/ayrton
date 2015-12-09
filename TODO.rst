Even when most of these are in the github issues, I leave it here so I can
attack it offline (when I code best).

Really do:
----------

* better error reporting, including remotes

* interface so local and remote can easily setup more communication channels

* we're weeding out imports, we could gather a list and reimport them in the
  remote

   * from foo import bar is gonna break

* imported ayrton scripts should be parsed with the ayrton parser.

* becareful with if cat () | grep (); error codes must be carried too

* exit code of last Command should be used as return code of functions

* process substitution

   * https://github.com/amoffat/sh/issues/66

* enable tracing

   * see pdb's source

* becareful with buitins, might eclipse valid usages: bash() (exp) blocks /bin/bash
   * rename bash() to expand()
   * add option _exec=True for actually executing the binary.

* check ``bash``'s manpage and see what's missing.
* subprocess

   * with ayrton (): ...

* a setting for making references to unkown envvars as in bash.
* trap?
* executable path caching à la bash.

Think deeply about:
-------------------

* what to do about relative/absolute command paths?
* git (commit) vs git.commit() vs git ('commit')
* function names are expressions too:
    * / as unary op? => /path/to/excecutable and relative/path
    * foo_bar vs foo__bar vs foo-bar
    * -f vs (-)f vs _f
* commands in keywords should also be _out=Capture
* which is the sanest default, bash (..., single=True) or otherwise
