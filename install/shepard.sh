#!/usr/bin/bash

set -o errexit
set -x

echo "Installing system dependencies"
sudo apt install python3 python3-pip python3-venv

echo "Installing submodules"
git submodule update --init --recursive

echo "Installing pip dependencies"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Running tests (sanity check)"
./scripts/test.sh

echo "Installing shepard.service"
sudo ln install/shepard.service /etc/systemd/system
sudo systemctl enable mavlink-router.service

echo "Installation complete. You will have to reboot for the installation to take effect"
