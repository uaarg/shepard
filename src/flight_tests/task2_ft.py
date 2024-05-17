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
WAY_POINT1 = [53.496500, -113.551900]
WAY_POINT2 = [53.497400, -113.551900]
#WAY_POINT3 = [53.496588, -113.548689]

#Hard coded position which is 5m away from the waypoint

MOVE_MARK1 = [53.496450, -113.551850]
MOVE_MARK2 = [53.497450, -113.551850]

waypoint1_location_global = LocationGlobal(WAY_POINT1[0], WAY_POINT1[1], ALTITUDE)
waypoint2_location_global = LocationGlobal(WAY_POINT2[0], WAY_POINT2[1], ALTITUDE)
waypoint3_location_global = LocationGlobal(WAY_POINT3[0], WAY_POINT3[1], ALTITUDE)


movemark1_location_global = LocationGlobal(MOVE_MARK1[0], MOVE_MARK1[1], ALTITUDE)
movemark2_location_global = LocationGlobal(MOVE_MARK2[0], MOVE_MARK2[1], ALTITUDE)



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


# Predecided number of laps for the drone to complete (This will later be adjusted based on battery consumption)

laps = 2

for i in range(laps)
    nav.send_status_message("Moving Around Waypoint 1")
    nav.set_altitude_position(movemark1_location_global.lat,movemark1_location_global.lon,movemark1_location_global.alt)
    nav.set_altitude_position_relative(-5, 5, ALTITUDE)
    nav.set_altitude_position_relative(5, 5, ALTITUDE)


    nav.send_status_message("Moving Around Waypoint 2")
    nav.set_altitude_position(movemark2_location_global.lat,movemark2_location_global.lon,movemark2_location_global.alt)
    nav.set_altitude_position_relative(5, -5, ALTITUDE)
    nav.set_altitude_position_relative(-5, -5, ALTITUDE)

    nav.send_status_message("Completed Lap " + str(i) + "out of " + str(i) + " laps")


nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")
