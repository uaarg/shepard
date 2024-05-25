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

first_location = LocationGlobal(ALPHA[0], ALPHA[1], 100)

nav.set_position_relative(0, 0)
drone.groundspeed = SPEED

nav.set_altitude_position_relative(0, 0, 100)

nav.set_altitude_position(first_location.lat,
                          first_location.lon,
                          first_location.alt)

nav.return_to_launch()

drone.close()

nav.send_status_message("Shepard execution terminated")
