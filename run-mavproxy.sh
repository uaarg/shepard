#!/usr/bin/env bash

mavproxy.py --master /dev/ttyS0,57600 --out /dev/ttyUSB0,57600 --show-errors --mav20 --daemon
