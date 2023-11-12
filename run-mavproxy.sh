#!/usr/bin/env bash

mavproxy.py --master /dev/ttyS0,57600 --out /dev/ttyUSB0,57600 --out 127.0.0.1:14550 --out 127.0.0.1:14551 --master 127.0.0.1:14560 --show-errors --mav20 --daemon --streamrate=1
