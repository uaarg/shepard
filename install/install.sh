#!/usr/bin/bash

set -o errexit

sudo apt update
sudo apt upgrade

sudo apt install python3-pyqrcode

echo "Setting up ssh keys"
./install/setup-ssh-keys.sh

echo "Installing mavlink router"
./install/mavlink-router.sh

echo "Installing shepard"
./install/shepard.sh
