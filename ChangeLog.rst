ayrton (0.7.1) UNRELEASED; urgency=medium

  * Iterable parameters to executables are expanded in situ, so `foo(..., i, ...)` is expanded to `foo (..., i[0], i[1], ...` and `foo(..., k=i, ...)` is expanded to `foo (..., k=i[0], k=i[1], ...`.
  * `-x|--trace` allows for minimal execution tracing.
  * `-xx|--trace-with-linenos` allows for execution tracing that also prints the line number.

 -- Marcos Dione <mdione@grulic.org.ar>  Wed, 03 Feb 2016 10:29:40 +0100

ayrton (0.7) unstable; urgency=medium

  * Send data to/from the remote via another `ssh` channel, which is more stable than using `stdin`.
  * Stabilized a lot all tests, specially those using a mocked stdout for getting test validation.
  * A lot of tests have been moved to their own scripts in ayrton/tests/scripts, which also work as (very minimal) examples of whatś working.
  * Use `flake8` to check the code.
  * Move `remote()` to its own source.
  * API change: if a `str` or `bytes` object is passed in `_in`, then it's the name of a file where to read `stdin`. If it's an `int`, then it's considered a file descriptor. This makes the API consistent to `_out` and `_err` handling.
  * More error handling.
  * Fixed errors with global variables handling.
  * `argv` is handled at the last time possible, allowing it being passed from test invoction.
  * `shift` complains on negative values.
  * Lazy `pprint()`, so debug statemens do not do useless work.
  * `stdin/out/err` handling in `remote()` is done by a single thread.
  * Modify a lot the local terminal when in `remote()` so, among other things, we have no local echo.
  * Properly pass the terminal type and size to the remote. These last three features allows programs like `vi` be run in the remote.
  * Paved the road to make `remote()`s more like `Command()`s.

 -- Marcos Dione <mdione@grulic.org.ar>  Wed, 09 Dec 2015 15:48:49 +0100

ayrton (0.6) unstable; urgency=medium

  * Great improvements in `remote()`'s API and sematics:
    * Made sure local varaibles go to and come back from the remote.
    * Code block is executes syncronically.
    * For the moment the streams are no longer returned.
    * _python_only option is gone.
    * Most tests actually connect to a listening netcat, only one test uses `ssh`.
  * Fixed bugs in the new parser.
  * Fixed globals/locals mix up.
  * Scripts are no longer wrapped in a function. This means that you can't return values and that module semantics are restored.
  * `ayrton` exits with status 1 when the script fails to run (SyntaxError, etc).

 -- Marcos Dione <mdione@grulic.org.ar>  Wed, 28 Oct 2015 20:57:19 +0100

ayrton (0.5) unstable; urgency=medium

  * Much better command detection.
  * `CommandNotFound` exception is now a subclass of `NameError`.
  * Allow `Command` keywords be named like `-l` and `--long-option`, so it supports options with single dashes (`-long-option`, à la `find`).
  * This also means that long-option is no longer passed as --long-option; you have to put the dashes explicitly.
  * bash() does not return a single string by default; override with single=True.
  * Way more tests.
  * Updated docs.

 -- Marcos Dione <mdione@grulic.org.ar>  Sun, 30 Aug 2015 15:13:30 +0200

ayrton (0.4.4) unstable; urgency=low

  * `source()` is out. use Python's import system.
  * Support executing `foo.py()`.

 -- Marcos Dione <mdione@grulic.org.ar>  Wed, 20 May 2015 23:44:42 +0200

ayrton (0.4.3) unstable; urgency=medium

  * Let commands handle SIGPIE and SIGINT. Python does funky things to them.
  * for line in foo(): ... forces Capture'ing the output.
  * Fix remote() a little. The API stills sucks.
  * Fix remote() tests.

 -- Marcos Dione <mdione@grulic.org.ar>  Fri, 10 Apr 2015 22:09:40 +0200

ayrton (0.4.2) unstable; urgency=low

  * _bg allows running a command in the background.
  * _fails allows a Command to fail even when option('-e') is on.
  * Try program_name as program-name if the first failed the path lookup.
  * Convert all arguments to commands to str().
  * chdir() is an alias of cd().
  * Capture is a class, not an arbitrary value.
  * Updated doc.
  * Fixed globals and local passed to the execution of the script.
  * Fixed some fd leakage.
  * Fixed redirection when _out and _err where Capture.
  * Fixed keyword handling while doing our black magic.
  * More, better unit tests!

 -- Marcos Dione <mdione@grulic.org.ar>  Wed, 14 Jan 2015 21:58:28 +0100

ayrton (0.4) unstable; urgency=low

  * >= can redirect stederr to stdout.
  * o(option=argument) can be used to declare keyword params among/before
    positional ones.
  * bash() now returns a single string if there is only one result.
  * Slightly better error reporting: don't print a part of the stacktrace
    that belongs to `ayrton` itself. There is still more to do.
  * No longer depends on `sh`.

 -- Marcos Dione <mdione@grulic.org.ar>  Tue, 14 Jan 2014 21:35:13 +0100

ayrton (0.3) unstable; urgency=low

  * Piping and basic redirection works.

 -- Marcos Dione <mdione@grulic.org.ar>  Thu, 03 Oct 2013 20:42:12 +0200

ayrton (0.2) unstable; urgency=low

  * New function `options()` is similar to `bash`'s `set` command. So far
    only the `errexit` and its short versions is accepted.
  * The `ssh()` context manager was renamed to `remote()`. See NEWS.rst.
  * New function `shitf()` similar to `bash`'s command of the same name.
    See the docs.

 -- Marcos Dione <mdione@grulic.org.ar>  Sat, 14 Sep 2013 17:59:27 +0200

ayrton (0.1.2) unstable; urgency=low

  * RunninCommand.exit_code is a property, not a function. Closes #13.

 -- Marcos Dione <mdione@grulic.org.ar>  Wed, 11 Sep 2013 19:38:12 +0200

ayrton (0.1.1) unstable; urgency=low

  * The remote code (the body of a `with ssh (..): ...`) can be either pure
    Python or ayrton. Pure Python imposes less dependencies on the remote.
  * You can access the original `argv` in the remote.
  * More documentation, more examples, even some that are useful!

 -- Marcos Dione <mdione@grulic.org.ar>  Wed, 11 Sep 2013 08:53:04 +0200

ayrton (0.1) unstable; urgency=low

  * Initial release.

 -- Marcos Dione <mdione@grulic.org.ar>  Sun, 09 Sep 2013 12:45:42 +0200
