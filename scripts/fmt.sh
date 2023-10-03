#!/usr/bin/env sh

yapf --parallel --in-place pylint $(git ls-files '*.py')
