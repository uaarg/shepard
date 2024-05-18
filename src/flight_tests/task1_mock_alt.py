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
start_coords = drone.location.global_relative_frame
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
#waypoint3_location_global = LocationGlobal(WAY_POINT3[0], WAY_POINT3[1], ALTITUDE)


movemark1_location_global = LocationGlobal(MOVE_MARK1[0], MOVE_MARK1[1], ALTITUDE)
movemark2_location_global = LocationGlobal(MOVE_MARK2[0], MOVE_MARK2[1], ALTITUDE)

distance_marks = nav.__get_distance_metres(movemark1_location_global, movemark2_location_global)


speed = 10

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


# https://mavlink.io/en/messages/common.html#SET_POSITION_TARGET_LOCAL_NED


# Predecided number of laps for the drone to complete (This will later be adjusted based on battery consumption)

laps = 2



nav.send_status_message("Moving Around Waypoint 1")
start_vector_distance = nav.__get_vector_distance(start_coords, movemark1_location_global)

start_x_distance = start_vector_distance[0]
start_y_distance = start_vector_distance[1]

nav.send_ned_velocity(-start_x_distance, start_y_distance)
nav.send_ned_velocity(-5, 5)
nav.send_ned_velocity(5, 5)

for i in range(laps):
    
    nav.send_status_message("Moving Around Waypoint 2")

    current_coords2 = drone.location.global_relative_frame

    point2_vector_distance = nav.__get_vector_distance(current_coords1, movemark2_location_global)
    point2_x_distance = point2_vector_distance[0]
    point2_y_disance = point2_vector_distance[1]

    nav.send_ned_velocity(point2_x_distance, -point2_y_disance)
    nav.send_ned_velocity(5, -5)
    nav.send_ned_velocity(-5, -5)

    current_coords1 = drone.location.global_relative_frame

    point1_vector_distance = nav.__get_vector_distance(current_coords1, movemark1_location_global)
    point1_x_distance = point1_vector_distance[0]
    point1_y_disance = point1_vector_distance[1]

    nav.send_ned_velocity(-point1_x_distance, point1_y_disance)
    nav.send_ned_velocity(-5, 5)
    nav.send_ned_velocity(5, 5)

    nav.send_status_message(f"Completed Lap {i} out of {laps} laps")

nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")



