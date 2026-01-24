#!/bin/bash
cd home/fawwaz
source sim/venv/bin/activate
cd code/shepard
PYTHONUNBUFFERED=1 PYTHONPATH=".:dep/labeller:dep/labeller/third_party/yolov5" python3 samples/bucket_test_simple.py
