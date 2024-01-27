#!/usr/bin/env bash

ssh-keygen
python3 install/setup-ssh-keys.py

echo "Add that key to github"
echo "Press enter when done"
read
