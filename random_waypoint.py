import argparse
from dronekit import connect, Command, VehicleMode, CommandSequence
from typing import Tuple
import random
from geopy.distance import distance as dt
import time


def generate_random_waypoint(current: Tuple[float, float],
                             bearing: Tuple[float, float] = (0, 360), distance: Tuple[float, float] = (50, 100)):
    """
    Generate a random waypoint near the given one

    :param current: Latitude and longitude of the given waypoint
    :param bearing: Range of direction the waypoint is generated, 0 - North, 90 - East, 180 - South, 270 - West
    :param distance: Range of the distance the new waypoint is located from the given one
    :return: A tuple of latitude and longitude of the generated waypoint
    """

    bearing = random.randint(*bearing)
    distance = random.randint(*distance)
    destination = dt(meters=distance).destination(current, bearing)
    (lat, long, alt) = destination
    return lat, long


def upload_waypoints(commands: CommandSequence, location: Tuple[float, float], altitude: float, verbose: bool = True):
    """
    Generate a random waypoint and upload the MavLink command

    :param commands: The CommandSequence instance used to upload the MavLink command
    :param location: The location of the waypoint
    :param altitude: The target altitude of the waypoint
    :param verbose: Verbosity, when set to True, print the location of the newly generated waypoint
    """

    waypoint = generate_random_waypoint(location)
    commands.add(Command(0, 0, 0, 3, 16, 0, 0, 0, 0, 0, 0, *waypoint, altitude))
    commands.upload()
    if verbose:
        print(f'New waypoint generated at {waypoint}')


# Parse command-line arguments
parser = argparse.ArgumentParser(description='Establish MavLink Connection')
parser.add_argument('--master', type=str, nargs='?', default='127.0.0.1:14550', help='port for MavLink connection')
parser.add_argument('--wait_ready', nargs='?', type=bool, default=False, const=True,
                    help='whether to wait for attribute download')
parser.add_argument('--altitude', '--alt', nargs='?', type=float, default='10',
                    help='default altitude of random generated waypoints')
args = parser.parse_args()

# Connect to vehicle
print(f'Connecting to {args.master}')
vehicle = connect(args.master, wait_ready=args.wait_ready)
print(f'Connected to vehicle on {args.master}')

# Create and start new mission
position = vehicle.location.global_relative_frame
position = (position.lat, position.lon)
print(f'Current location: {position}')
alt = args.altitude
print(f'Target altitude: {alt}')

cmds = vehicle.commands
cmds.clear()
upload_waypoints(cmds, position, alt)

vehicle.mode = VehicleMode('AUTO')
print('Starting mission')

# Generate random waypoint on-route
while True:
    cmds.download()
    cmds.wait_ready()
    if cmds.next == cmds.count:
        last_cmd = cmds[-1]
        location = (last_cmd.x, last_cmd.y)
        upload_waypoints(cmds, location, alt)
    time.sleep(1)
