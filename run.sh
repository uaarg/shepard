#!/usr/bin/env sh

echo 'Starting Shepard at' $(pwd)
python main.py --camera rpicam2 --port /dev/serial0,57600 --capture-rate=10
