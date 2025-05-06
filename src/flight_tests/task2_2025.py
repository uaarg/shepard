from typing import Optional
from src.modules.imaging.detector import IrDetector
import time
from src.modules.imaging.analysis import ImageAnalysisDelegate, DebugImageAnalysisDelegate
from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.location import DebugLocationProvider
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector
from src.modules.georeference import inference_georeference
from src.modules.imaging.kml import KMLGenerator, LatLong


from PIL import Image, ImageDraw
from src.modules.autopilot import lander
from src.modules.autopilot import navigator

from dronekit import connect, VehicleMode

import json

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

# How much we want to hover above the ground when we are filling or emptying
target_height = 1

bucket_avg = [[], []]


def moving_bucket_avg(_, pos):
    avg_x = sum(bucket_avg[0])
    avg_y = sum(bucket_avg[1])

    num_x = len(bucket_avg[0])
    num_y = len(bucket_avg[1])

    new_x_avg = avg_x + pos[0] / (num_x + 1)
    new_y_avg = avg_y + pos[1] / (num_y + 1)

    bucket_avg[0].append(new_x_avg)
    bucket_avg[1].append(new_y_avg)



camera = RPiCamera()
detector = IrDetector()
location = DebugLocationProvider()

# analysis = ImageAnalysisDelegate(detector, camera, location)
analysis = DebugImageAnalysisDelegate(camera)
analysis.x = 0  # CHANGE ME
analysis.y = 0  # CHANGE ME
analysis.subscribe(moving_bucket_avg)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

time.sleep(2)
analysis.start()


nav.takeoff(30)

type_mask = nav.generate_typemask([0, 1, 2])

nav.send_status_message("Executing")
current_alt = nav.get_local_position_ned()[2]


delta = 0.5
sleep_time = 2


# VERIFY ALL OF THESE COORINDATE SYSTEMS BEFORE FLYING!!!!!!!!!!!!!!!!!!!!!!!!!

nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 0, type_mask = type_mask)

time.sleep(5)

nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 10, type_mask = type_mask)

time.sleep(5)


nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 5, type_mask = type_mask)

time.sleep(5)


nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 5, type_mask = type_mask)

time.sleep(5)


nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 5, type_mask = type_mask)

time.sleep(5)


#Full commit


nav.set_position_target_local_ned(x = 0, y = 0, z = 5-target_height, type_mask = type_mask)

time.sleep(5)


