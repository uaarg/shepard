#!/usr/bin/bash

st -o errexit

echo "Installing mavlink router"
./mavlink-router.sh

echo "Installing shepard"
./shepard.sh
