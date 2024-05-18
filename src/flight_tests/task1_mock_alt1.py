import time

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

nav.POSITION_TOLERANCE = 5

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
time.sleep(2)

SPEED = 10  # m/s
ALTITUDE = 20  # m

WAYPOINT_1 = [53.497200, -113.548800]
WAYPOINT_2 = [53.497200, -113.551600]

waypoints = [[WAYPOINT_1[0] - 0.000050, WAYPOINT_1[1] + 0.000050],
             [WAYPOINT_1[0] + 0.000050, WAYPOINT_1[1] + 0.000050],
             [WAYPOINT_2[0] + 0.000050, WAYPOINT_2[1] - 0.000050],
             [WAYPOINT_2[0] - 0.000050, WAYPOINT_2[1] - 0.000050]]

locations = [LocationGlobal(wp[0], wp[1], ALTITUDE) for wp in waypoints]

nav.set_position_relative(0, 0)
nav.set_speed(SPEED)

LAPS = 5

for i in range(LAPS):
    for location in locations:
        nav.set_altitude_position(location.lat, location.lon, location.alt)

nav.return_to_launch()

drone.close()

nav.send_status_message("Shepard execution terminated")
