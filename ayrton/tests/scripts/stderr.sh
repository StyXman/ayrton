#! /bin/sh

if [ $# -eq 2 ]; then
    out="$1"
    err="$2"
else
    err="$1"
fi

if [ -n "$out" ]; then
    echo "$out"
fi

echo "$err" >&2
