#! /bin/bash

set -eu

pypy_src="$1"

# NOTE: not every Python version changes the syntax
for file in astcompiler/__init__.py \
            astcompiler/astbuilder.py \
            astcompiler/consts.py \
            astcompiler/misc.py \
            astcompiler/tools/Python.asdl \
            astcompiler/tools/asdl.py \
            astcompiler/tools/asdl_py.py \
            pyparser/__init__.py \
            pyparser/automata.py \
            pyparser/data/Grammar2.5 \
            pyparser/data/Grammar2.7 \
            pyparser/data/Grammar3.2 \
            pyparser/data/Grammar3.3 \
            pyparser/data/Grammar3.5 \
            pyparser/data/Grammar3.6 \
            pyparser/dfa_generated.py \
            pyparser/error.py \
            pyparser/future.py \
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

    mkdir --parents --verbose "$(dirname $dst)"
    cp --verbose "$src" "$dst"
done
