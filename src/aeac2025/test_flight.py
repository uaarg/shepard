import time

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator

CALLSIGN = "ALBERTA1"
CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14550

SPEED = 5

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")

nav.takeoff(10)

drone.groundspeed = SPEED
nav.set_position_relative(10, 0)


nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")

