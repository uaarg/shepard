from typing import Optional
from src.modules.imaging.bucket_detector import BucketDetector
import time
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.location import DebugLocationProvider
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector
from src.modules.georeference import inference_georeference
from src.modules.imaging.kml import KMLGenerator, LatLong
from pymavlink import mavutil


from PIL import Image, ImageDraw
from src.modules.autopilot import lander
from src.modules.autopilot import navigator

from dronekit import connect, VehicleMode

import json

import os

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

time.sleep(2)

bucket_avg = [[], []]
target_height = 0.9


os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs)
os.makedirs(f"tmp/log/{ft_num}")


def moving_bucket_avg(_, pos):

    if pos:
        if len(bucket_avg[0]) > 0 and len(bucket_avg[1]) > 0:

                num_x = len(bucket_avg[0])
                num_y = len(bucket_avg[1])

                avg_x = sum(bucket_avg[0]) / num_x
                avg_y = sum(bucket_avg[1]) / num_y

                new_x_avg = avg_x + pos[0] / (num_x + 1)
                new_y_avg = avg_y + pos[1] / (num_y + 1)

                bucket_avg[0].append(new_x_avg)
                bucket_avg[1].append(new_y_avg)
        else:
            bucket_avg[0].append(pos[0])
            bucket_avg[1].append(pos[1])
        
        print(f"X: {bucket_avg[0]}")
        print(f"Y: {bucket_avg[1]}")
        time.sleep(1)



camera = RPiCamera(0)

model_file = "11n640.pt"

detector = BucketDetector(f"samples/models/{model_file}")
location = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(moving_bucket_avg)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

time.sleep(5)
analysis.start()


nav.takeoff(30)

type_mask = nav.generate_typemask([0, 1, 2])

nav.send_status_message("Executing")
current_alt = nav.get_local_position_ned()[2]



delta = 0.5
sleep_time = 2

def bucket_descent():

   
# VERIFY ALL OF THESE COORINDATE SYSTEMS BEFORE FLYING!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED

    nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 0, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)

    nav.set_position_target_local_ned(x = (bucket_avg[0][-1] - bucket_avg[0][0]), y = (bucket_avg[1][-1] - bucket_avg[1][0]), z = 10, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)

    nav.set_position_target_local_ned(x = (bucket_avg[0][-1] - bucket_avg[0][0]), y = (bucket_avg[1][-1], bucket_avg[1][0]), z = 5, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)


    nav.set_position_target_local_ned(x = (bucket_avg[0][-1] - bucket_avg[0][0]), y = (bucket_avg[1][-1] - bucket_avg[1][0]), z = 5, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)


    nav.set_position_target_local_ned(x = (bucket_avg[0][-1] - bucket_avg[0][0]), y = (bucket_avg[1][-1] - bucket_avg[1][0]), z = 5, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)


    #Full commit

    nav.set_position_target_local_ned(x = 0, y = 0, z = 5-target_height, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)




if len(bucket_avg[0]) > 0 and len(bucket_avg[1]) > 0:
   bucket_descent()
else:
    time.sleep(5)
    bucket_descent()

nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")


