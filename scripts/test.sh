#!/usr/bin/env sh

export PYTHONPATH=".:src/modules/mavctl:src/modules/mavctl/mavctl"
pytest
