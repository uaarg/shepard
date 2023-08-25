import argparse
from dronekit import connect
from mission import gps_to_cartesian, Mission
from tree import (set_start_waypoint, set_skipped_points,
                  create_safe_waypoints, find_valid_connections)
import matplotlib.pyplot as plt
import math
import cv2
import time
import csv
from qr import qr


def dijkstra(conns, coords):
    visitedNodes = {}
    distances = {}
    camefrom = {}
    for i in conns:
        if i[0] not in visitedNodes:
            visitedNodes[i[0]] = False
        if i[1] not in visitedNodes:
            visitedNodes[i[1]] = False
    distances['S'] = 0

    for i in visitedNodes:
        if i != 'S':
            distances[i] = 999999

    currentNode = 'S'
    while not visitedNodes['T']:
        print("new visitedNode")
        print(currentNode)
        for i in range(len(conns)):
            if conns[i][0] == currentNode:
                if not visitedNodes[conns[i][1]]:
                    point1 = coords[i][0]
                    point2 = coords[i][1]
                    dist = math.sqrt(((point1[0] - point2[0])**2) +
                                     ((point1[1] - point2[1])**2))
                    print("updating distance between " + conns[i][0] +
                          " and " + conns[i][1])
                    if dist == min(dist, distances[conns[i][1]]):
                        distances[conns[i][1]] = dist
                        camefrom[conns[i][1]] = conns[i][0]
                    print(min(dist, distances[conns[i][1]]))
        visitedNodes[currentNode] = True
        minDist = 999999
        for i in visitedNodes:
            if not visitedNodes[i]:
                minDist = min(distances[i], minDist)
        node = None
        for i in distances:
            if distances[i] == minDist:
                node = i
        currentNode = node
    print(distances)

    current = 'T'
    path = [current]
    while current in camefrom:
        current = camefrom[current]
        path.append(current)
    path.reverse()
    return path


def parse_args():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Establish MAVLink Connection')
    parser.add_argument('--master',
                        type=str,
                        nargs='?',
                        default='127.0.0.1:5762',
                        help='port for MAVLink connection')
    parser.add_argument('--wait_ready',
                        nargs='?',
                        type=bool,
                        default=False,
                        const=True,
                        help='whether to wait for attribute download')
    parser.add_argument('--altitude',
                        '--alt',
                        nargs='?',
                        type=float,
                        default='50',
                        help='default altitude of generated gps waypoints')
    args = parser.parse_args()
    return args


def load_waypoints(
        file_name: str = '../competition_waypoints/competition_waypoints.csv',
        encoding: str = 'UTF-8'):
    waypoints = dict()
    with open(file_name, encoding=encoding) as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            waypoints[row[0]] = tuple(map(float, row[1:]))
    print(waypoints)
    return waypoints


def parse_qr(args, file_name='../competition_waypoints/task1_avoidance.txt'):
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


if __name__ == '__main__':
    args = parse_args()

    # Connect to vehicle
    print(f'Connecting to {args.master}')
    vehicle = connect(args.master, wait_ready=args.wait_ready, baud=57600)
    print(f'Connected to vehicle on {args.master}')
    cmds = vehicle.commands

    # download unfinished commands
    cmds.download()
    cmds.wait_ready()
    next_waypoint_number = cmds.next - 1 if cmds.next > 0 else 1
    unfinished_commands = list(cmds)[next_waypoint_number:]
    waypoints_gps = [(cmd.x, cmd.y) for cmd in unfinished_commands]
    print('waypoints_gps:', waypoints_gps)

    # load all available waypoints
    waypoints = load_waypoints()
    waypoints_list = list(waypoints.keys())

    # # parse obstacle sequence
    # text = parse_qr(args)
    # print(f"{text = }")
    # region, rejoin_point = parse.parse_task1_avoidance(text)
    # print(f"{region = }")
    # print(f"{rejoin_point = }")
    # obstacle_gps = [waypoints[i] for i in region]
    # print(f"{obstacle_gps = }")

    # # load avoidance area (test)
    with open('../tests/south_campus/south_campus_task1_avoidance_area.poly',
              encoding='UTF-8') as poly_file:
        poly_reader = csv.reader(poly_file, delimiter=' ')
        next(poly_reader, None)  # Skip header
        obstacle_gps = [tuple(map(float, coord)) for coord in poly_reader]
    print('obstacle_gps:', obstacle_gps)
    test_waypoints = Mission.load_from_waypoint(
        '../tests/south_campus/south_campus_task1_test_waypoints.waypoints')
    test_gps_coordinates = test_waypoints.xy[1:]
    print('test_gps_coordinates:', test_gps_coordinates)

    # convert to cartesian coordinates
    nodes = dict()
    waypoints_cartesian, origin_gps = gps_to_cartesian(waypoints_gps)
    print('waypoints_cartesian:', waypoints_cartesian)
    print('origin_gps:', origin_gps)
    obstacle_cartesian = gps_to_cartesian(obstacle_gps, origin_gps)[0]
    print('obstacle_cartesian:', obstacle_cartesian)
    # rejoin_point_cartesian = gps_to_cartesian([waypoints[rejoin_point]], origin_gps)[0]
    rejoin_point_cartesian = gps_to_cartesian([test_gps_coordinates[5]],
                                              origin_gps)[0]  # Test
    print('rejoin_point_cartesian:', rejoin_point_cartesian)

    # generate node
    nodes['T'] = [*rejoin_point_cartesian[0], 'target']
    for iter, obstacle in enumerate(obstacle_cartesian):
        nodes['obstacle_' + str(iter)] = [*obstacle, 'obstacle']
    for iter, waypoint in enumerate(waypoints_cartesian):
        nodes[str(iter + 1)] = [*waypoint, 'waypoint']

    print('nodes:', nodes)

    # plot path and obstacle
    plt.plot(*list(zip(*waypoints_cartesian)))
    obstacle_plot = obstacle_cartesian + [obstacle_cartesian[0]]
    plt.plot(*list(zip(*obstacle_plot)))
    plt.scatter(*list(zip(*rejoin_point_cartesian)), c='r')
    plt.show()

    # generate connections
    nodes, start_point = set_start_waypoint(nodes, margin=1.1)
    print(f'{start_point = }')
    print(f'{nodes[start_point][:2] = }')
    print('nodes:', nodes)
    nodes, skipped_points = set_skipped_points(nodes)
    print(f'{skipped_points = }')

    # generate nodes for dijkstra
    nodes_dijkstra = dict()
    for name, data in nodes.items():
        if data[2] == 'target' or data[2] == 'obstacle':
            nodes_dijkstra[name] = data
        elif data[2] == 'start':
            nodes_dijkstra['S'] = data
    print(f'{nodes_dijkstra = }')

    waypoints, nofly_region, margin_region = create_safe_waypoints(
        nodes_dijkstra, margin=1.1)
    connections, coords = find_valid_connections(waypoints, nofly_region,
                                                 margin_region)
    print(f"{connections = }\n{coords = }")

    # find the shortest path
    distances = dijkstra(connections, coords)
    new_waypoints_cartesian = [
        tuple(map(float, waypoints[waypoint])) for waypoint in list(distances)
    ]
    print(f"{new_waypoints_cartesian = }")

    # complete flight path
    unrouted1 = waypoints_cartesian[:waypoints_cartesian.
                                    index(tuple(nodes[start_point][:2]))]
    print(f"{unrouted1 = }")
    if len(skipped_points) != 0:
        last_skipped = 0
        for point in skipped_points:
            if waypoints_cartesian.index(nodes[point]) > last_skipped:
                last_skipped = waypoints_cartesian.index(nodes[point][:2])
        unrouted2 = waypoints_cartesian[last_skipped + 1:]
    else:
        unrouted2 = waypoints_cartesian[waypoints_cartesian.
                                        index(tuple(nodes[start_point][:2])) +
                                        1:]
    print(f"{unrouted2 = }")
    new_waypoints_cartesian = unrouted1 + new_waypoints_cartesian + unrouted2
    print(f"{new_waypoints_cartesian = }")

    # plot new path and obstacle
    plt.plot(*list(zip(*new_waypoints_cartesian)))
    obstacle_plot = obstacle_cartesian + [obstacle_cartesian[0]]
    plt.plot(*list(zip(*obstacle_plot)))
    plt.show()

    # ## convert back to gps
    # new_waypoints = cartesian_to_gps(new_waypoints_cartesian, origin_gps)
    # alt = args.altitude
    # cmds.clear()
    # for waypoint in new_waypoints:
    #     cmds.next = 1
    #     cmds.add(Command(0, 0, 0, 3, 16, 0, 0, 0, 0, 0, 0, *waypoint, alt))
    # vehicle.wait_ready(True, raise_exception=False)
    # cmds.upload()
