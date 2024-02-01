#!/usr/bin/env bash

set -o errexit

sample="$1"

if ! git status 2>&1 >/dev/null; then
  echo "Please run this script from inside the shepard repository"
  exit 1
fi

#cd "$(git worktree list | awk '{ print $1 }')"

if ! test -f "samples/$sample.py"; then
  echo "ERROR: Please pass a sample which is one of:"
  ls samples/*.py | sed 's/^samples\// - /' | sed 's/\.py$//'
  exit 1
fi

PYTHONPATH=".:dep/labeller" python3 "samples/$sample.py"
