#!/usr/bin/env sh

echo 'Starting Shepard at' $(pwd)
python main.py --camera rpicam2 --port /dev/ttyS0
