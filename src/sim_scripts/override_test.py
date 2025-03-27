import time
import datetime

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass


nav.set_position_target_local_ned(x = 10, y = 10, vx=2, vy=3)
time.sleep(0.2)

nav.set_position_target_local_ned(x=-30, y=-30, z=20, vx=3, vy=4)
time.sleep(0.2)

nav.set_position_target_local_ned(x=50, y=50, vx=10, vy=10)
time.sleep(0.2)

nav.cancel_command()
time.sleep(0.2)

nav.return_to_launch()

drone.close()

nav.send_status_message("Shepard execution terminated")
