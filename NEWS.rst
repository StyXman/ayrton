ayrton (0.4) UNRELEASED; urgency=low

  * bash() now returns strings if the result would be a list with only 
    one string.

 -- Marcos Dione <mdione@grulic.org.ar>  Mon, 28 Oct 2013 17:40:49 -0300

ayrton (0.2) unstable; urgency=low

  * The `ssh()` context manager was renamed to `remote()` so the `ssh`
    executable is stills reachable from code. This was due to the fact
    that `ssh` is too complex to mimic.

 -- Marcos Dione <mdione@grulic.org.ar>  Sat, 14 Sep 2013 17:59:27 +0200
