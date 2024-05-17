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
#drone.groundspeed = 2  # m/s
# start_coords = drone.location.global_relative_frame
time.sleep(2)

MAX_GROUND_SPEED = 20
TIME = 180  #3 minutes
ALTITUDE = 15
WAY_POINT1 = [53.497385, -113.551907]
WAY_POINT2 = [53.496030, -113.551961]
WAY_POINT3 = [53.496588, -113.548689]


location_global1 = LocationGlobal(WAY_POINT1[0], WAY_POINT1[1], ALTITUDE)
location_global2 = LocationGlobal(WAY_POINT2[0], WAY_POINT2[1], ALTITUDE)
location_global3 = LocationGlobal(WAY_POINT3[0], WAY_POINT3[1], ALTITUDE)

speed = nav.optimum_speed(TIME,[location_global1,location_global2,location_global3])

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

nav.send_status_message("Moving to Location 1")
nav.set_altitude_position(location_global1.lat,location_global1.lon,location_global1.alt)

nav.send_status_message("Moving to Location 2")
nav.set_altitude_position(location_global2.lat,location_global2.lon,location_global2.alt)

nav.send_status_message("Moving to Location 3")
nav.set_altitude_position(location_global3.lat,location_global3.lon,location_global3.alt)


nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")
