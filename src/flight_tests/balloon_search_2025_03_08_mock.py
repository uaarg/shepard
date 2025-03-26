
import math
# import os
# import threading
# import time
from PIL import Image

# from dronekit import connect, VehicleMode

# from src.modules.autopilot import navigator
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.location import DebugLocationProvider
# from src.modules.autopilot.altimeter_xm125 import XM125
# from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider
from dep.labeller.benchmarks.detector import BoundingBox

# from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.camera import DebugCameraFromDir
from src.modules.imaging.detector import BalloonDetector
from PIL import Image, ImageDraw

new_inference = False
found_balloon = False
direction = None
distance = None

def update_inference(img: Image.Image, bb : BoundingBox | None):
    """subscribed to ImageAnalysisDelegate"""
    global new_inference
    global direction
    global distance
    global found_balloon
    if bb is not None:
        found_balloon = True
        # draw enlarged square centred on middle of balloon
        draw = ImageDraw.Draw(img)
        draw.rectangle((bb.position.x - 25, bb.position.y - 25, bb.position.x + 50, bb.position.y +  50), (0, 255, 0), 10)
        img.show()

        w, _ = img.size # get width of image for consistency regardless of size

        if bb.position.x >= w * 0.7:
            direction = "right"
            distance = bb.position.x - (w // 2)
        elif bb.position.x <= w * 0.3:
            direction = "left"
            distance = bb.position.x 
        else:
            direction = "center"
            distance = 0
    else:
        img.show()
        found_balloon = False
    # update new_inference after to ensure we do not use incorrect data in main loop
    new_inference = True

# Imaging setup
detector = BalloonDetector()
# camera = RPiCamera()
camera = DebugCameraFromDir("photos") # choose directory where photos are located
location_provider = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector=detector, camera=camera, location_provider=location_provider)
analysis.subscribe(update_inference)
analysis.start()

movement_amnt = 60
turn_count = 0
step_size = 1  # meters

while turn_count < 6: # 60 degrees * 6 = 360 => we completed a full circle without finding balloons
    if new_inference == True: # there is a new inference else keep looping and waiting
        if found_balloon == True:
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

        else: # we did not see the balloon
            print("no balloon")
            if direction is None:
                turn_count += 1
                print("No balloons detected")
                # fov is around 62 degrees so if we move 30 degrees either direction we get a (mostly) new image
                print("set_heading_relative(60)")
            else:
                # we previously saw a balloon which we do not anymore
                if direction == "right":
                    # if previously moved right balloon would be to the left
                    print("set_heading_relative(-movement_amnt)")
                elif direction == "left":
                    # if previously moved left balloon would be to the right 
                    print("set_heading_relative(movement_amnt)")
                else:
                    print("wtf")
        
        new_inference = False

