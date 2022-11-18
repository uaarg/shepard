#   UAARG - Autopilot 2022
"""
This file tests the connection to autopilot software using drone-kit via MAVLink
"""

import argparse
from dronekit import connect, VehicleMode
from math import pi
from time import sleep


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Establish MAVLink Connection')
parser.add_argument('--master', type=str, nargs='?', default='127.0.0.1:14550', help='port for MAVLink connection')
parser.add_argument('--wait_ready', nargs='?', type=bool, default=False, const=True,
                    help='whether to wait for attribute download')
args = parser.parse_args()

# Connect to vehicle
print(f'Connecting to {args.master}')
vehicle = connect(args.master, wait_ready=args.wait_ready)

while True:
    # Retrieve status of vehicle
    roll = vehicle.attitude.roll*180/pi
    mode = vehicle.mode
    print(roll)

    # Change mode based on vehicle status
    if roll < 0 and mode != VehicleMode('MANUAL'):
        vehicle.mode = VehicleMode('MANUAL')
    elif roll > 0 and mode != VehicleMode('RTL'):
        vehicle.mode = VehicleMode('RTL')

    sleep(1)
