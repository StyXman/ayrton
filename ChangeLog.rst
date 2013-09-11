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
