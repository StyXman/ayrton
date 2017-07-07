#! /bin/sh

case "$1" in
    -c|--clean)
        shift
        make testclean
        break;;
    *)
        break;;
esac

exec python3 -m unittest -v ayrton.tests.$1
