#!/usr/bin/env bash

set -o errexit
set -x

echo "Installing wget"
sudo apt install wget

echo "Downloading Python3.10"
wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz

echo "Installing Python SSL Modules"
sudo apt install libssl-dev libxslt-dev
#libncurses5-dev libsqlite3-dev libreadline-dev libtk8.6 libgdm-dev libdb4o-cil-dev libpcap-dev

echo "Untarring Python file"
tar xf Python-3.10.13.tgz

echo "Installing Python"
cd Python-3.10.13/
./configure
make
sudo make install
