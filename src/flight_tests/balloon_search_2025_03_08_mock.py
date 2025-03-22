import math
import os
import threading
import time
from PIL import Image

from dronekit import connect, VehicleMode

from src.modules.autopilot import navigator
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.location import DebugLocationProvider
from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider
from dep.labeller.detector import BoundingBox

from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.detector import Detector

new_inference = True
direction = None
distance = None

def update_inference(img: Image.Image, bb: BoundingBox):
    """subscribed to ImageAnalysisDelegate"""
    img.show()

    global direction
    global distance
    global new_inference

    new_inference = True

    if bb.position.x >= 1200:
        direction = "right"
        distance = bb.position.x - 960
    elif bb.position.x <= 720:
        direction = "left"
        distance = bb.position.x 
    else:
        direction = "center"
        distance = 0


# Imaging setup
detector = Detector()
camera = RPiCamera()
location_provider = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector=detector, camera=camera, location_provider=location_debugger)
analysis.subscribe(update_inference)
analysis.start()




prev_movement_dir = None
movement_amnt = 60
turn_count = 0

while turn_count < 6: # 60 degrees * 6 = 360 => we completed a full circle without finding balloons
    step_size = 1  # meters

    if not new_inference:
        direction = None
        distance = None 

    if direction is not None: # we saw balloon
        prev_movement_dir = direction # keep track in case balloon goes out of frame after previously found
        #movement_amnt //= 2
        print(f"Balloon detected: Move {direction}, Distance: {distance:.2f}")

        if direction == "center":
            # Move in that direction, need to calculate the N and E offsets based on heading
            current_heading = 0
            metres_north_relative = step_size * math.sin(math.radians(current_heading))
            metres_east_relative = step_size * math.cos(math.radians(current_heading))
            print(metres_north_relative, metres_east_relative)

        # best thing we could do is calculate the angle required to centre it
        # could also keep halving the distance
        elif direction == "right":
            # nav.set_heading_relative(movement_amnt/(distance/960))
            print(f"setting heading right {movement_amnt/(distance/960)}")
        elif direction == "left":
            # nav.set_heading_relative(movement_amnt/(distance/960))
             print(f"setting heading left {movement_amnt/(distance/960)}")

    else: # we did nto see the balloon
        if prev_movement_dir == None:
            turn_count += 1
            print("No balloons detected")
            # fov is around 62 degrees so if we move 30 degrees either direction we get a (mostly) new image
            print("set_heading_relative(60)")
        else:
            # we previously saw a balloon which we do not anymore
            movement_amnt //= 2
            if prev_movement_dir == "right":
                print("set_heading_relative(-movement_amnt)") # if previously moved right balloon would be to the left
            else:
                print("set_heading_relative(movement_amnt)")
    
    new_inference = False