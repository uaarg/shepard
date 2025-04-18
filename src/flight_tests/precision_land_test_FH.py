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

from src.modules.imaging import analysis
from src.modules.imaging import camera
from src.modules.imaging import debug
from src.modules.imaging import location
from dep.labeller.benchmarks import yolo

mavlink_delegate = location.MAVLinkDelegate()
location_provider = location.MAVLinkLocationProvider(mavlink_delegate)
location_provider = location.DebugLocationProvider()
location_provider.debug_change_location(altitude=1)

detector = yolo.YoloDetector(weights="landing_nano.pt")
cam = camera.RPiCamera()
debugger = debug.ImageAnalysisDebugger()
debugger = None
img_analysis = analysis.ImageAnalysisDelegate(detector, cam, location_provider,
                                              debugger)
mavlink_delegate.run()

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander()
altimeter = altimeter.XM125(average_window=5)
altimeter.begin()


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
precision_land_enable = False


img_analysis.subscribe(lambda _, x, y: precision_land(x, y))
img_analysis.start()



waypoint = [10, 10, 20]


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

precision_land_enable = True

type_mask = nav.generate_typemask([0, 1, 2])

current_alt = drone.location.global_relative_frame.alt

def precision_land(x, y):

    # NEEDS TO BE MODIFIED TO ACTUALLY GO TO COORDINATES RELEVATIVE TO THE ORIGIN OF THIS REFERENCE FRAME
    current_alt = drone.location.global_relative_frame.alt
    if precision_land_enable and current_alt >= 0.5:
        nav.set_position_target_local_ned(x = x, y = y, z = 0, type_mask=type_mask)
    elif current_alt < 0.5:
        nav.land()
        precision_land_enable = False

