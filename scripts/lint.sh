#!/usr/bin/env sh

flake8 --max-line-length 140 --ignore E265,F541,F811,W504,E402 $(git ls-files '*.py')
