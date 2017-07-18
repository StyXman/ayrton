#! /bin/bash

set -eu

cpython_src="$1"
pypy_src="$2"

fun copy() {
    src="$1"
    dst="$2"

    mkdir --parents --verbose "$(dirname $dst)"
    cp --verbose "$src" "$dst"
}

# NOTE: not every Python version changes the syntax
for file in astcompiler/__init__.py \
            astcompiler/astbuilder.py \
            astcompiler/consts.py \
            astcompiler/misc.py \
            pyparser/__init__.py \
            pyparser/automata.py \
            pyparser/data/Grammar2.5 \
            pyparser/data/Grammar2.7 \
            pyparser/data/Grammar3.2 \
            pyparser/data/Grammar3.3 \
            pyparser/data/Grammar3.5 \
            pyparser/data/Grammar3.6 \
            pyparser/error.py \
            pyparser/future.py \
            pyparser/gendfa.py \
            pyparser/metaparser.py \
            pyparser/parser.py \
            pyparser/pygram.py \
            pyparser/pyparse.py \
            pyparser/pytoken.py \
            pyparser/pytokenize.py \
            pyparser/pytokenizer.py \
            __init__.py \
            debug.py \
            error.py; do
    src="$pypy_src/pypy/interpreter/$file"
    dst="ayrton/parser/$file"

    copy("$src", "$dst")
done

# run generators
# ayrton/parser/pyparser/dfa_generated.py
PYTHONPATH=$(pwd) \
    ./ayrton/parser/pyparser/gendfa.py | \
    python3.6 -c 'import sys; data = sys.stdin.read(); open(sys.argv[1], "w+").write(data)' \
    ./ayrton/parser/pyparser/dfa_generated.py
