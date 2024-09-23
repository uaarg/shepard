from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

nav.POSITION_TOLERANCE = 5

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")

nav.takeoff(10)

SPEED = 10  # m/s
CRUISE_ALT = 20  # m
MAX_ALT = 105

ALPHA = [48.51127, -71.65054]
BRAVO = [48.50586, -71.63222]

first_location = LocationGlobal(ALPHA[0], ALPHA[1], MAX_ALT)

nav.set_position_relative(0, 0)
drone.groundspeed = SPEED

nav.set_altitude(MAX_ALT)

nav.set_altitude_position(first_location.lat, first_location.lon,
                          first_location.alt)

nav.return_to_launch()

drone.close()

nav.send_status_message("Shepard execution terminated")
