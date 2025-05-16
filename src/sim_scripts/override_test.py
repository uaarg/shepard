import time
import numpy as np

from dronekit import connect, VehicleMode

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

type_mask = nav.generate_typemask([0, 1, 2, 4])

nav.send_status_message("Executing")

nav.takeoff(10)

delta = 2
sleep_time = 2

hover_alt = 10

current_alt = nav.get_local_position_ned()[2]
print(current_alt)

points = [(0, 0), (0, 1), (1, 1), (1, 0)]
i = 0


while np.abs(current_alt) >= 0.5:
    # Generate random points to simulate the changes
    # x = random.rand() * delta
    # y = random.rand() * delta

    print(i)
    location = nav.get_local_position_ned()
    current_alt = location[2]
    print(current_alt)
    nav.set_position_target_local_ned(x = 0, y = i * delta, z = -hover_alt, vy = 2, type_mask = type_mask)

    i += 1
    time.sleep(0.5)

nav.return_to_launch()
time.sleep(2)
drone.close()

nav.send_status_message("Shepard execution terminated")
