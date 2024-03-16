#!/usr/bin/env bash

logfile="log/$(date +'%x-%X').log"
mkdir -p "$(dirname "$logfile")"
PYTHONPATH="." python3 src/flight_tests/ft_current.py 2>&1 | tee "$logfile"
