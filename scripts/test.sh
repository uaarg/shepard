#!/usr/bin/env sh

PYTHONPATH=".:dep/labeller" pytest --ignore=src/modules/mavctl
