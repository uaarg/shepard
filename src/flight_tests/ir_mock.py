from typing import Optional
from src.modules.imaging.detector import IrDetector
import time
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.location import DebugLocationProvider
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector
from PIL import Image, ImageDraw
from src.modules.autopilot import lander
from src.modules.autopilot import navigator


CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

MAX_VELOCITY = 1

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
lander = lander.Lander(nav, MAX_VELOCITY)

    
camera = RPiCamera()
detector = IrDetector()
location = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(lander.detectBoundingBox)

analysis.start()

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

nav.send_status_message("Executing mission")
time.sleep(2)

nav.takeoff(10)
drone.groundspeed = 2  # m/s
# start_coords = drone.location.global_relative_frame
time.sleep(2)

nav.set_altitude_position_relative(20, 0, 10)
time.sleep(1)


nav.send_status_message("Executing landing pad search")
lander.generateRoute(4)

nav.send_status_message(lander.route)

for route in lander.route:
    lander.goNext(route, 10)
    time.sleep(5)

# nav.set_position(start_coords.lat, start_coords.lon)
# time.sleep(1)
# nav.land()

nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")

detected = False
time1 = 0

# def func(image: Image.Image, bb: [BoundingBox]):
   # global time1

