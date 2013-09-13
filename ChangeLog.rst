ayrton (0.2) UNRELEASED; urgency=low

  * New function `options()` is similar to `bash`'s `set` command. So far
    only the `errexit` and its short versions is accepted.
  * The `ssh()` context manager was renamed to `remote()`. See NEWS.rst.
  * New function `shitf()` similar to `bash`'s command of the same name.
    See the docs.

 -- Marcos Dione <mdione@grulic.org.ar>  Fri, 13 Sep 2013 13:43:25 +0200

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
