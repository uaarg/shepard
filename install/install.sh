#!/usr/bin/bash

st -o errexit

echo "Installing mavlink router"
./install/mavlink-router.sh

echo "Installing shepard"
./install/shepard.sh
