import time

from dronekit import connect, VehicleMode

from src.modules.autopilot import navigator

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
start_coords = drone.location.global_relative_frame
time.sleep(2)

# set tolerance higher to avoid issues
nav.POSITION_TOLERANCE = 2  # metres

# Fly back and forth pattern
delta_EW = 160  # metres, distance back and forth East-West
delta_NS = 10  # metres, distance to go north each iteration
total_NS = 135  # metres, total distance to fly north

travelled_NS = 0

while travelled_NS <= total_NS:
    # fly west first
    nav.set_position_relative(0, -delta_EW)
    # fly north a bit
    nav.set_position_relative(delta_NS, 0)
    # fly back east
    nav.set_position_relative(0, delta_EW)
    # fly north again a bit
    nav.set_position_relative(delta_NS, 0)

    travelled_NS += 20

    
nav.precision_landing(start_coords.lat, start_coords.lon, start_coords.alt)


drone.close()
nav.send_status_message("Flight test script execution terminated")
