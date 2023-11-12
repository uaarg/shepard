import time

from dronekit import connect, VehicleMode

from src.modules.autopilot import navigator
from src.modules.autopilot import lander


# TODO: Add connection string
CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14550

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

nav.send_message("SHEPARD: status message functional.")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.takeoff(20)
drone.groundspeed = 5  # m/s

# Fly a square with 50 m side lengths

# Test landing pad search sequence
lander.generateRoute(3)
lander.goNext(nav, lander.route, drone.location.global_relative_frame.alt)

# RTL
nav.return_to_launch()

drone.close()
