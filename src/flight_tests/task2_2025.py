from typing import Optional
from src.modules.imaging.bucket_detector import BucketDetector
import time
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import RPiCamera, DebugCamera
from src.modules.imaging.location import DebugLocationProvider, LocationProvider, MAVLinkLocationProvider
from src.modules.imaging.mavlink import MAVLinkDelegate
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

import RPi.GPIO as GPIO

CONN_STR = "udp:127.0.0.1:14551"
MESSENGER_PORT = 14552
mavlink_str = "udp:127.0.0.1:14553"
GPIO_PIN = 23


drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
mavlink = MAVLinkDelegate(conn_str = mavlink_str)


GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)
GPIO.output(23, GPIO.HIGH)

time.sleep(2)

GPIO.output(23, GPIO.LOW)


bucket_avg = [[], []]
big_bucket_height = 1


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
        
        time.sleep(1)



camera = DebugCamera("photos/7.png")

model_file = "best.pt"

detector = BucketDetector(f"samples/models/{model_file}")


analysis = ImageAnalysisDelegate(detector, camera, navigation_provider = nav)
analysis.subscribe(moving_bucket_avg)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

time.sleep(5)


nav.takeoff(30)

type_mask = nav.generate_typemask([0, 1, 2])

nav.send_status_message("Executing")
current_alt = nav.get_local_position_ned()[2]



delta = 0.5
sleep_time = 2
def bucket_descent(target_height):
    

# VERIFY ALL OF THESE COORINDATE SYSTEMS BEFORE FLYING!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED

    nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 0, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)
    alt = nav.get_local_position_ned()[2]
    i = 0
    while -(alt) >= 11:
        print(i) 

        alt = nav.get_local_position_ned()[2]

        print(alt)
        nav.set_position_target_local_ned(x = float(bucket_avg[0][-1] - bucket_avg[0][0]), y = float(bucket_avg[1][-1] - bucket_avg[1][0]), z = 5, type_mask = type_mask, coordinate_frame = coordinate_frame)
        i += 1
        time.sleep(5)

    # Full Commit, drone is set to hover at the target height
    # NOTE: COORDINATE SYSTEM HAS CHANGED. IT IS IN NED, DOWN IS POSITIVE

    nav.send_status_message("Comitting to bucket")
    coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_NED
    current_local_pos = nav.get_local_position_ned()
    
    nav.set_position_target_local_ned(x = current_local_pos[0], y = current_local_pos[1], z = -target_height, type_mask = type_mask, coordinate_frame = coordinate_frame)


def ActivatePump(duration):
    coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_NED
    current_local_pos = nav.get_local_position_ned()
    # Runs the pump that is connected to GPIO 23 for a specified amount of time
    
    nav.set_position_target_local_ned(x = current_local_pos[0], y = current_local_pos[1], z = current_local_pos[2], type_mask = type_mask, coordinate_frame = coordinate_frame)

    GPIO.output(GPIO_PIN, GPIO.HIGH)
   
    # Make sure that the drone maintains its location above the bucket, hopefully avoiding drift due to wind or other sources
    # Adjusts the drones position every half second, and the duration is equivalent to the duration passed to ActivatePump()
    for _ in range(duration - 1):
   
        nav.set_position_target_local_ned(x = current_local_pos[0], y = current_local_pos[1], z = current_local_pos[2], type_mask = type_mask, coordinate_frame = coordinate_frame)
        time.sleep(0.5)
       
        nav.set_position_target_local_ned(x = current_local_pos[0], y = current_local_pos[1], z = current_local_pos[2], type_mask = type_mask, coordinate_frame = coordinate_frame)
        time.sleep(0.5)


    GPIO.output(GPIO_PIN, GPIO.LOW)


nav.send_status_message("Descending to bucket")
analysis.start()
time.sleep(5)
if len(bucket_avg[0]) > 0 and len(bucket_avg[1]) > 0:
   bucket_descent(big_bucket_height)
else:
    time.sleep(5)
    bucket_descent(big_bucket_height)
analysis.stop()
nav.send_status_message("Stopped the analysis")

nav.send_status_message("Activating Pump")

ActivatePump(5)

nav.return_to_launch()

drone.close()

nav.send_status_message("Flight test script execution terminated")


