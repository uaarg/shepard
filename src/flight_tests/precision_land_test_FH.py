'''
Idea behind this flight test script is to fly to a waypoint and test the built-in precision landing component. 

Eventually this script will be adapted to support the ability to send rangefinder data to the pixhawk so that more accurate precision landing is possible. 

'''

import time
import threading

from dronekit import connect, VehicleMode, LocationGlobal

from src.modules.autopilot import navigator
from src.modules.autopilot import lander
import src.modules.autopilot.altimeter as altimeter
import src.modules.autopilot.altimeter_poll as poll

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()
altimeter = altimeter.XM125(average_window=5)
altimeter.begin()


# Initialize a new thread which continuously polls the altimeter and will (hopefully) send the altimeter data to the pixhawk
thread1 = threading.Thread(target = poll.poll(altimeter=altimeter))
thread1.start()

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

waypoint = [53.497332, -113.550619, 30]


# MODIFY THIS AS REQUIRED
speed = nav.optimum_speed(TIME, [waypoint])

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


nav.send_status_message(f"Moving to pre-set waypoints")
nav.set_altitude_position(waypoint[0],
                            waypoint[1],
                            waypoint[2],
                            battery=None,
                            hard_cutoff_enable=False)



# Invokes the implementation of the built-in precision landing function. 
nav.precision_landing(start_coords.lat, start_coords.lon, start_coords.alt)

