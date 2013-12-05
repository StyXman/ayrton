ayrton (0.4) UNRELEASED; urgency=low

  * >= can redirect stederr to stdout.
  * o(option=argument) can be used to declare keyword params among/before 
    positional ones.
  * bash() now returns a single string if there is only one result.
  * Slightly better error reporting: don't print the part of the stacktrace
    that belongs to `ayrton` itself.

 -- Marcos Dione <mdione@diablo>  Thu, 05 Dec 2013 13:33:07 +0100

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
