import argparse
from dronekit import connect, VehicleMode
from time import sleep

parser = argparse.ArgumentParser(description='Establish MavLink Connection')
parser.add_argument('master', type=str, nargs='+', default='127.0.0.1:14550', help='port for MavLink connection')
parser.add_argument('--wait_ready', type=bool, nargs=1, default=False, const=True,
                    help='whether to wait for attribute download')

args = parser.parse_args()

print(f'Connecting to {args.master}')
vehicle = connect(args.master, wait_ready=args.wait_ready)

while True:
    roll = vehicle.attitude.roll
    mode = vehicle.mode
    print(roll)

    if roll < 0 and mode != VehicleMode('MANUAL'):
        vehicle.mode = VehicleMode('MANUAL')
    elif mode != VehicleMode('RTL'):
        vehicle.mode = VehicleMode('RTL')

    sleep(1)
