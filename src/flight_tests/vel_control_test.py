import time
import datetime
from numpy import random

from dronekit import connect, VehicleMode, LocationGlobal
from pymavlink import mavutil

from src.modules.autopilot import navigator
from src.modules.autopilot import lander

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
#lander = lander.Lander()

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

time.sleep(2)

nav.takeoff(10)

type_mask = nav.generate_typemask([0, 1, 2])

nav.send_status_message("Executing")
current_alt = nav.get_local_position_ned()[2]

delta = 1
steps = 10
max_velocity = 0.5

hover_alt = 10

print(current_alt)

route = []


for i in range(int(round(-current_alt) - 1)):
    nav.set_position_target_local_ned(x = 0, y = 0, z = 1, type_mask = type_mask, coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
    time.sleep(2)
print("Stage one complete")

for i in range(9):
    current_pos = nav.get_local_position_ned()
    print(current_pos)
    nav.set_position_target_local_ned(x = current_pos[0], y = current_pos[1], z = current_pos[2] + 0.1*i, type_mask = type_mask)
    time.sleep(1)
print("Stage two complete")


current_pos = nav.get_local_position_ned()
nav.set_position_target_local_ned(x = current_pos[0], y = current_pos[1], z = 0, type_mask = type_mask)


route.append(0)
print(route)

i = 0


time.sleep(2)
nav.land()
time.sleep(2)
drone.close()

nav.send_status_message("Shepard execution terminated")
