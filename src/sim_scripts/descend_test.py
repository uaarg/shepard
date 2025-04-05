import time
import datetime
from numpy import random

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

time.sleep(2)

nav.takeoff(10)

type_mask = nav.generate_typemask([0, 1, 2])

nav.send_status_message("Executing")
current_alt = nav.get_local_position_ned()[2]

delta = 0.5
sleep_time = 2

hover_alt = 10

print(current_alt)

points = [(0, 0), (0,1), (1,1), (1,0)]
i = 0
j = 0

nav.set_position_target_local_ned(x = points[0][0] * delta, y = points[0][1] * delta, z = -10, type_mask = type_mask)

while j <= 3:
    if i == 0:
        nav.set_position_target_local_ned(x = points[0][0] * delta, y = points[0][1] * delta, z = -10, type_mask = type_mask)
        time.sleep(5)
        i = 1
    else:
        nav.set_position_target_local_ned(x = points[0][0] * delta, y = points[0][1] * delta, z = -5, type_mask = type_mask)
        time.sleep(10)
        i = 0
    j += 1

nav.return_to_launch()
time.sleep(2)
drone.close()

nav.send_status_message("Shepard execution terminated")
