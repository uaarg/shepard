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


nav.takeoff(30)
time.sleep(2)

type_mask = nav.generate_typemask([0, 1, 2])

nav.send_status_message("Executing First Waypoint")
nav.set_position_target_local_ned(x = 50, y = 0, z = 20, type_mask = type_mask)


time.sleep(20)
'''
nav.send_status_message("Executing Second Waypoint")
nav.set_position_target_local_ned(x=-30, y=0, z=20, vx=3, vy=4, vz = 0, type_mask = type_mask)
time.sleep(10)
'''
nav.return_to_launch()
time.sleep(2)
drone.close()

nav.send_status_message("Shepard execution terminated")
