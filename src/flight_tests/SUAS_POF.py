import time

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(20)
time.sleep(2)

MAX_GROUND_SPEED = 20
ALTITUDE = 30 
LAPS = 3

waypoints = [[53.49595, -113.55451],
             [53.49727, -113.55440],
             [53.49712, -113.54405],
             [53.49587, -113.54400]
             ]

start_point = [53.49568, -113.54944]

locations = [LocationGlobal(wp[0], wp[1], ALTITUDE) for wp in waypoints]

# workaround to get the speed to set properly for the actual waypoints
nav.set_position_relative(0, 0)

time.sleep(1)
nav.set_speed(speed)
time.sleep(1)

nav.set_altitude_position(start_point[0],
                        start_point[1],
                        ALTITUDE)

for _ in range(LAPS - 1):
    for i, location in enumerate(locations):
        nav.send_status_message(f"Moving to waypoint {i + 1} of {len(locations)}")
        nav.set_altitude_position(location.lat,
                                location.lon,
                                ALTITUDE)

nav.set_altitude_position(start_point[0],
                        start_point[1],
                        ALTITUDE)

time.sleep(2)
nav.return_to_launch()
drone.close()

nav.send_status_message("Flight test script execution terminated")
