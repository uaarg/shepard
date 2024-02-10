#!/usr/bin/bash

set -o errexit
set -x

echo "Installing submodules"
git submodule update --init --recursive

echo "Installing system dependencies"
sudo apt install cmake libgl1-mesa-glx

echo "Installing pip dependencies"
python3.10 -m pip install --upgrade pip setuptools wheel
python3.10 -m pip install -r requirements.txt

echo "Running tests (sanity check)"
export PYTHONPATH=".:dep/labeller:dep/labeller/third_party/yolov5"
python3.10 -m pytest

echo "Installing shepard.service"
sudo ln install/shepard.service /etc/systemd/system
sudo systemctl enable shepard.service

echo "Installation complete. You will have to reboot for the installation to take effect"
