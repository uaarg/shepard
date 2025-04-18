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


    # global detected
    # top_left_corner: Tuple[float, float] = (bb.position.x, bb.position.y)
    # bottom_right_corner: Tuple[float, float] = (bb.position.x + bb.size.x,
    #                                             bb.position.y + bb.size.y)
    #
    # draw = ImageDraw.Draw(image)
    # draw.rectangle((top_left_corner, bottom_right_corner), outline="red", width=3)
    #

camera = RPiCamera()
detector = IrDetector()
location = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(func)

analysis.start()



nav.send_status_message("Executing landing pad search")
lander.generateSpiralSearch(4)

nav.send_status_message(lander.route)

lander.executeSearch(10)
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

