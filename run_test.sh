#! /bin/sh

case "$1" in
    -n|--no-clean)
        shift
        break;;
    *)
        make testclean
        break;;
esac

exec python3.6 -m unittest -v ayrton.tests.$1
