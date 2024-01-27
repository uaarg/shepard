#!/usr/bin/env bash

set -o errexit
set -x

echo "Installing dependencies"
sudo apt install -y git meson ninja-build pkg-config gcc g++ systemd

echo "Building mavlink-router"
git clone --recursive https://github.com/mavlink-router/mavlink-router
cd mavlink-router/
meson setup build .
ninja -C build

echo "Installing mavlink-router"
sudo ninja -C build install

echo "Setting up system files"
sudo cp -r system/etc/mavlink-router /etc
sudo cp system/boot/config.txt /boot/config.txt

sudo systemctl enable mavlink-router.service

echo "Mavlink router install complete"
echo "Please restart with 'sudo reboot' so the changes can take effect"
