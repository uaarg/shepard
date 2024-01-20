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

sudo mkdir /etc/mavlink-router
sudo cat >/etc/mavlink-router/main.conf <<EOF
[General]
TcpServerPort=14550

[UartEndpoint px4]
Device = /dev/ttyS0
Baud = 57600

[UartEndpoint xbee]
Device = /dev/ttyUSB0
Baud = 57600
EOF

sudo systemctl enable mavlink-router.service

echo "Mavlink router install complete"
echo "Please restart with 'sudo reboot' so the changes can take effect"
