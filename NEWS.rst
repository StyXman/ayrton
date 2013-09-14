ayrton (0.2) UNRELEASED; urgency=low

  * The `ssh()` context manager was renamed to `remote()` so the `ssh`
    executable is stills reachable from code. This was due to the fact 
    that `ssh` is too complex to mimic.

 -- Marcos Dione <mdione@grulic.org.ar>  Fri, 13 Sep 2013 13:47:26 +0200
