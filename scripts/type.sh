#!/usr/bin/env sh

export PYTHONPATH="."

echo "Checking imaging modules"
mypy --check-untyped-defs --ignore-missing-imports src/modules/imaging/*.py

echo "Checking tests"
mypy --ignore-missing-imports test/*.py
