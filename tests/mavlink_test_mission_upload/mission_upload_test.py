#   UAARG - Autopilot 2022
"""
This file tests the mission upload function of drone-kit via MAVLink
"""

import argparse
from dronekit import connect, Command
import mission as mi

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Establish MAVLink Connection')
# parser.add_argument('--master', type=str, nargs='?', default='127.0.0.1:14550', help='port for MAVLink connection')
parser.add_argument('--master', type=str, nargs='?', default='com3', help='port for MAVLink connection')
parser.add_argument('--wait_ready', nargs='?', type=bool, default=False, const=True,
                    help='whether to wait for attribute download')
args = parser.parse_args()

# Connect to vehicle
print(f'Connecting to {args.master}')
vehicle = connect(args.master, wait_ready=args.wait_ready, baud=57600)

# Get the set of commands from the vehicle
cmds = vehicle.commands
# cmds.download()
# cmds.wait_ready()

# Load, create and add commands
test_mission = mi.Mission.load_from_wkt('test_waypoints/2023_AEAC_Task_Waypoints.csv')
mission_matrix = test_mission.to_dronekit()
for mission in mission_matrix:
    cmds.add(Command(*mission))

cmds.upload()  # Send commands
print('Mission uploaded')
