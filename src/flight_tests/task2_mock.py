import time

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

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
start_coords = drone.location.global_relative_frame
time.sleep(2)

MAX_GROUND_SPEED = 20
TIME = 5 * 60  # 5 minutes
ALTITUDE = 15

waypoints = [[53.497332, -113.550619, 30], [53.496801, -113.550650, 25],
             [53.496801, -113.549702, 20], [53.496917, -113.549702, 19],
             [53.496975, -113.549616, 18], [53.497028, -113.549499, 17],
             [53.497061, -113.549299, 16], [53.497056, -113.549003, 15],
             [53.497302, -113.548999, 12.5],
             [start_coords.lat, start_coords.lon, 10]]

locations = [LocationGlobal(wp[0], wp[1], wp[2]) for wp in waypoints]

speed = nav.optimum_speed(TIME, locations)

#checking to ensure ground speed is safe
assert speed > 0
assert speed < MAX_GROUND_SPEED

#drone.groundspeed = speed
#nav.send_status_message(f"Ground speed set to {speed} m/s")

# workaround to get the speed to set properly for the actual waypoints
nav.set_position_relative(0, 0)

time.sleep(1)
nav.set_speed(speed)
time.sleep(1)

for i, location in enumerate(locations):
    nav.send_status_message(f"Moving to waypoint {i + 1} of {len(locations)}")
    nav.set_altitude_position(location.lat,
                              location.lon,
                              location.alt,
                              battery=None,
                              hard_cutoff_enable=False)

nav.land()

drone.close()

nav.send_status_message("Flight test script execution terminated")
