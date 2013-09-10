Even when most of these are in the github issues, I leave it here so I can
attack it offline (when I code best).

Really do:
----------

* source
* shift
* better error reporting, including remotes
* better sh() interface (streams? yuk!)
* we're weeding out imports, we could gather a list and reimport them in the
  remote

   * from foo import bar is gonna break

* if we can implement |, then no function nesting

   * | is implementable, implement __ror__() for RunningCommandWrapper

      * it doesn't work, __ror__() is not called and in any case it's
        already too late, cat and grep have benn already called when
        __or__ is called (with two RunningCommandWrapper instances)

      * becareful with if cat () | grep (); error codes must be carried too

* process substitution

   * https://github.com/amoffat/sh/issues/66

* enable tracing

   * see pdb's source

* referencing non-existant envvars (FOO) is replaced by a Runner.
* becareful with buitins, might eclipse valid usages: bash() (exp) blocks /bin/bash

   * add option _exec=Ture for actually executing the binary.

* check ``bash``'s manpage and see what's missing.
* subprocess + redirection (...) > foo.txt

   * with ayrton (): ...

* a setting for making references to unkown envvars as in bash.
* trap?

If we {have time,are bored}:
----------------------------

* what to do about relative/absolute command paths?
* better error reporting
* | (pipe)
* redirections, if we ever implement |
* executable path caching à la bash.
