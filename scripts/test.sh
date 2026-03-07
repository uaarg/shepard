#!/usr/bin/env sh

pip install -e src/modules/mavctl

PYTHONPATH="." pytest
