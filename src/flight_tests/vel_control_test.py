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
steps = 5
max_velocity = 2

hover_alt = 10

print(current_alt)


route = []

def generate_points():
    for x in range(steps):
        route.append(current_alt + x * delta)
    for x in range(steps):
        route.append(route[-1] - x * delta)

for point in route:
    nav.set_position_target_local_ned(x = 0, y = 0, z = point, type_mask = type_mask, coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
    time.sleep(1/(max_velocity))

nav.return_to_launch()
time.sleep(2)
drone.close()

nav.send_status_message("Shepard execution terminated")
