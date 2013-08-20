# Really do:

* if we can implement |, then no function nesting
    * | is implementable, implement __ror__() for RunningCommandWrapper
        * it doesn't work, __ror__() is not called and in any case it's
          already too late, cat and grep have benn already called when
          __or__ is called (with two RunningCommandWrapper instances)
        * becareful with if cat () | grep (); error codes must be carried too
* process substitution
* document
* enable tracing
* referencing non-existant envvars (FOO) is replaced by a Runner.
* becareful with buitins, might eclipse valid usages: bash() (exp) blocks /bin/bash
* envvars as local vars.
* check `bash`'s manpage and see what's missing.

# If we {have time,are bored}:
* what to do about relative/absolute command paths?
* better error reporting
* revert commit 18e7bc5.
* |
* redirections, if we ever implement |
* with ssh (...): ...
