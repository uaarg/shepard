import time

from dronekit import connect, VehicleMode

from src.modules.autopilot import navigator
from src.modules.autopilot import lander

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

nav.send_status_message("Shepard is online.")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing...")

nav.takeoff(20)
drone.groundspeed = 5  # m/s

nav.set_position_relative(10, 10)
time.sleep(5)

nav.set_heading(0)
time.sleep(5)

nav.set_heading_relative(45)
time.sleep(5)

nav.set_heading_relative(45)
time.sleep(5)

nav.set_altitude(30)
time.sleep(5)

nav.set_altitude_relative(-10)
time.sleep(5)

nav.set_altitude_position_relative(-20, 0, 20)
time.sleep(10)

