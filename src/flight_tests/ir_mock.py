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

from dronekit import connect, VehicleMode


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
lander.generateSpiralSearch(4)

nav.send_status_message(lander.route)

bounding_boxes = lander.executeSearch(10)
# nav.set_position(start_coords.lat, start_coords.lon)
# time.sleep(1)
# nav.land()

with open("/tmp/IR_sites.txt", "w") as f:
    f.write(str(bounding_boxes))

nav.send_status_message("Bounding Box coordinates: " + str(bounding_boxes))

nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")

# def func(image: Image.Image, bb: [BoundingBox]):
   # global time1

