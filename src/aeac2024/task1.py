import time

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander

from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.imaging.battery import MAVLinkBatteryStatusProvider

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

nav.POSITION_TOLERANCE = 5

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
time.sleep(2)

SPEED = 10  # m/s
CRUISE_ALT = 20  # m

ALPHA = [48.51127, -71.65054]
BRAVO = [48.50586, -71.63222]

waypoints = [[ALPHA[0] - 0.000100, ALPHA[1] + 0.000050],
             [ALPHA[0] - 0.000050, ALPHA[1] + 0.000200],
             [ALPHA[0] + 0.000050, ALPHA[1] + 0.000200],
             [ALPHA[0] + 0.000100, ALPHA[1] + 0.000050],
             [BRAVO[0] + 0.000100, BRAVO[1] - 0.000050],
             [BRAVO[0] + 0.000050, BRAVO[1] - 0.000200],
             [BRAVO[0] - 0.000050, BRAVO[1] - 0.000200],
             [BRAVO[0] - 0.000100, BRAVO[1] - 0.000050]]

first_location = LocationGlobal(ALPHA[0], ALPHA[1], 100)
lap_locations = [LocationGlobal(wp[0], wp[1], CRUISE_ALT) for wp in waypoints]

nav.set_position_relative(0, 0)
drone.groundspeed = SPEED

nav.set_altitude_position(first_location.lat,
                          first_location.lon,
                          first_location.alt)

LAPS = 1

for i in range(LAPS):
    nav.send_status_message(f"Lap {i+1} of {LAPS}")
    for location in lap_locations:
        nav.set_altitude_position(location.lat, location.lon, location.alt)

for location in lap_locations[0:3]:
    nav.set_altitude_position(location.lat, location.lon, location.alt)

nav.return_to_launch()

drone.close()

nav.send_status_message("Shepard execution terminated")
