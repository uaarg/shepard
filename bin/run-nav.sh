#!/usr/bin/env bash

source venv/bin/activate
logfile="log/$(date +'%x-%X').log"
imgfile="log/$(date +'%x-%X').imglog"
mkdir -p "$(dirname "$logfile")"
mkdir -p "$(dirname "$imgfile")"

PYTHONUNBUFFERED=1 PYTHONPATH=".:dep/labeller:dep/labeller/third_party/yolov5" python3 samples/oakd.py 1>&1 | tee "$logfile" 
