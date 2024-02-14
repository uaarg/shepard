#!/usr/bin/bash

set -o errexit

sudo apt update
sudo apt upgrade

echo "installing mavlink router"
./install/mavlink-router.sh

echo "installing python3.10"
./install/openhd-python.sh

echo "Installing shepard"
./install/openhd-shepard.sh
