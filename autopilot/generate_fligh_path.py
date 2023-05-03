import argparse
from dronekit import connect, Command, VehicleMode, CommandSequence
from mission import gps_to_cartesian, cartesian_to_gps
from tree import *
import matplotlib.pyplot as plt
import math
from geopy.distance import distance as dt
from random import choice
import cv2
import time
from qr import qr, parse


def parse_args():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Establish MAVLink Connection')
    parser.add_argument('--master', type=str, nargs='?', default='127.0.0.1:5762', help='port for MAVLink connection')
    parser.add_argument('--wait_ready', nargs='?', type=bool, default=False, const=True,
                        help='whether to wait for attribute download')
    parser.add_argument('--altitude', '--alt', nargs='?', type=float, default='50',
                        help='default altitude of generated gps waypoints')
    args = parser.parse_args()
    return args


def load_waypoints(file_name: str = '../competition_waypoints/competition_waypoints.csv', encoding: str = 'UTF-8'):
    waypoints = dict()
    with open(file_name, encoding=encoding) as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            waypoints[row[0]] = tuple(map(float, row[1:]))
    print(waypoints)
    return waypoints


def upload_waypoints(cmds: Command, path, args):
    alt = args.altitude
    cmds.clear()
    for waypoint in path:
        cmds.next = 1
        cmds.add(Command(0, 0, 0, 3, 16, 0, 0, 0, 0, 0, 0, *waypoint, alt))
    cmds.upload()


def parse_qr(args, file_name = '../competition_waypoints/task1_route.txt'):
    cam = cv2.VideoCapture(0)
    cv2.namedWindow("view")

    time_start = time.time()
    while True:
        ret, frame = cam.read()
        if not ret:
            print("Frame grab failed.")
            break
        cv2.imwrite("inter.png", frame)
        cv2.imshow("view", frame)

        read = qr.readQRCode("inter.png")
        if read != "":
            cam.release()
            cv2.destroyAllWindows()
            print(read)
            return read
        else:
            print("no qr code/text found.")

        time_now = time.time()
        if time_now - time_start >= 10:
            break
        time.sleep(1)

    with open(file_name) as file:
        text = file.read()
    cam.release()
    cv2.destroyAllWindows()
    return text


def main(args):
    # Connect to vehicle
    print(f'Connecting to {args.master}')
    vehicle = connect(args.master, wait_ready=args.wait_ready, baud=57600)
    print(f'Connected to vehicle on {args.master}')
    cmds = vehicle.commands

    # load all available waypoints
    waypoints = load_waypoints()
    waypoints_list = list(waypoints.keys())

    # parse waypoint sequence (test)
    # plan = [choice(waypoints_list) for i in range(27)]
    # print(f"{plan = }")
    # path = [waypoints[i] for i in plan]
    # print(f"{path = }")

    # parse waypoint sequence
    text = parse_qr(args)
    print(f"{text = }")
    plan = parse.parse_task1_route(text)
    print(f"{plan = }")
    path = [waypoints[i] for i in plan]
    print(f"{path = }")

    #upload flight plan
    print("Waiting for vehicle to be ready...")
    vehicle.wait_ready(True, raise_exception=True, timeout=300)
    print(f"{vehicle.parameters = }")
    print("Vehicle ready. Uploading mission...")
    upload_waypoints(cmds, path, args)

if __name__ == "__main__":
    args = parse_args()
    main(args)