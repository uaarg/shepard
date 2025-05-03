#!/usr/bin/env bash

source venv/bin/activate
logfile="log/$(date +'%x-%X').log"
mkdir -p "$(dirname "$logfile")"
PYTHONUNBUFFERED=1 PYTHONPATH=".:dep/labeller:dep/labeller/third_party/yolov5" python3 src/flight_tests/SUAS_POF.py 2>&1 | tee "$logfile"
