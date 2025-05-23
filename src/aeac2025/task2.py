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
from http.server import HTTPServer, SimpleHTTPRequestHandler 

import os

import RPi.GPIO as GPIO

import threading

os.makedirs("tmp/video_server/", exist_ok=True)
cam1 = RPiCamera(1)
cam0 = RPiCamera(0)

IMG_DIR = "current_img.webp"
STEP_SIZE = 0.1
# ------------------------------------------
# this is stupid
# ------------------------------------------


class MyHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # If the request is for the root, serve index.html
        if self.path == '/':
            self.path = 'src/aeac2025/index.html'
        else:
            img = cam1.capture()
            # img.resize((960, 540))
            img.resize((480, 270))
            img.save(IMG_DIR)


        return super().do_GET()
    
    def do_POST(self):
        type_mask = nav.generate_typemask([0, 1, 2])
        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED

        if self.path == '/left':
            self.send_response(200)
            self.end_headers()
            # nav.set_position_relative(0, -STEP_SIZE)
            nav.set_position_target_local_ned(x = 0, y = -STEP_SIZE, z = 0, type_mask = type_mask, coordinate_frame = coordinate_frame)
        elif self.path == '/right':
            self.send_response(200)
            self.end_headers()
            # nav.set_position_relative(0, STEP_SIZE)
            nav.set_position_target_local_ned(x = 0, y = STEP_SIZE, z = 0, type_mask = type_mask, coordinate_frame = coordinate_frame)
        elif self.path == '/up':
            self.send_response(200)
            self.end_headers()            
            # nav.set_position_relative(STEP_SIZE, 0)
            nav.set_position_target_local_ned(x = STEP_SIZE, y = 0, z = 0, type_mask = type_mask, coordinate_frame = coordinate_frame)
        elif self.path == '/down':
            self.send_response(200)
            self.end_headers()
            # nav.set_position_relative(-STEP_SIZE, 0)
            nav.set_position_target_local_ned(x = -STEP_SIZE, y = 0, z = 0, type_mask = type_mask, coordinate_frame = coordinate_frame)

        elif self.path == '/ascend':
            self.send_response(200)
            self.end_headers()
            # nav.set_altitude_relative(STEP_SIZE)
            nav.set_position_target_local_ned(x = 0, y = 0, z = -STEP_SIZE, type_mask = type_mask, coordinate_frame = coordinate_frame)

        elif self.path == '/descend':
            self.send_response(200)
            self.end_headers()
            # nav.set_altitude_relative(-STEP_SIZE)
            nav.set_position_target_local_ned(x = 0, y = 0, z = STEP_SIZE, type_mask = type_mask, coordinate_frame = coordinate_frame)

        elif self.path == '/activate_pump':
            self.send_response(200)
            self.end_headers()
            GPIO.output(GPIO_PIN, GPIO.HIGH)

        elif self.path == '/deactivate_pump':
            self.send_response(200)
            self.end_headers()
            GPIO.output(GPIO_PIN, GPIO.LOW)

        else:
            print("invalid thingy")

    def log_message(self, format, *args):
        return

class WebServer:

    def __init__(self, port):

        self.port = port
        self.server = None
    
    def run(self):

        #setup server
        self.server = HTTPServer(('0.0.0.0', self.port), MyHandler) # Empty string means localhost
        print(f"Server running on http://localhost:{self.port}")
        self.server.serve_forever()


def run_server():
    # start the webserver
    server = WebServer(8081)
    server.run()


CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14550
GPIO_PIN = 23

SOURCE = [50.09800088902783, -110.73675825983138]
TARGET_1 = [50.098703093054226, -110.73533184525492]


# These are if we are feeling quite daring
TARGET_2 = [50.098799215198234, -110.73433402333168]
TARGET_3 = [50.09844193444824, -110.73416636293038]


drone = connect(CONN_STR, wait_ready=False)
print("Task2 script connected!")
nav = navigator.Navigator(drone, MESSENGER_PORT)

GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)
GPIO.output(23, GPIO.LOW)

thread = threading.Thread(target=run_server)
thread.start()

bucket_avg = [[], []]
big_bucket_height = 3
small_bucket_height = 3 

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
def clear_bucket_avg():
    bucket_avg = [[], []]



model_file = "best.pt"

detector = BucketDetector(f"samples/models/{model_file}")


analysis = ImageAnalysisDelegate(detector, cam0, navigation_provider = nav)
analysis.subscribe(moving_bucket_avg)

nav.send_status_message("Shepard is online")

while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
    pass

time.sleep(5)


nav.send_status_message("Executing")
nav.takeoff(20)

type_mask = nav.generate_typemask([0, 1, 2])

def bucket_descent(target_height):
    

# VERIFY ALL OF THESE COORINDATE SYSTEMS BEFORE FLYING!!!!!!!!!!!!!!!!!!!!!!!!!!
    
    coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED

    nav.set_position_target_local_ned(x = bucket_avg[0][-1], y = bucket_avg[1][-1], z = 0, type_mask = type_mask, coordinate_frame = coordinate_frame)

    time.sleep(5)
    alt = nav.get_local_position_ned()[2]
    while -(alt) >= 10:
        alt = nav.get_local_position_ned()[2]
        print(alt)
        nav.set_position_target_local_ned(x = float(bucket_avg[0][-1] - bucket_avg[0][0]), y = float(bucket_avg[1][-1] - bucket_avg[1][0]), z = 1, type_mask = type_mask, coordinate_frame = coordinate_frame)
        time.sleep(5)



    nav.send_status_message("Ready to continue autonomous descent?")
    while True:
        response = input("Type Done or skip")
        if response.lower() == "done":
                        
            # Full Commit, drone is set to hover at the target height
            # NOTE: COORDINATE SYSTEM HAS CHANGED. IT IS IN NED, DOWN IS POSITIVE

            nav.send_status_message("Comitting to bucket")
            coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_NED
            current_local_pos = nav.get_local_position_ned()
            for i in range(5):

                nav.set_position_target_local_ned(x = current_local_pos[0], y = current_local_pos[1], z = -(10 - i), type_mask = type_mask, coordinate_frame = coordinate_frame)

                time.sleep(5)
   
            nav.set_position_target_local_ned(x = current_local_pos[0], y = current_local_pos[1], z = -3, type_mask = type_mask, coordinate_frame = coordinate_frame)



            break

        elif response.lower() == "skip":
            break
        else:
            pass

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

while True: 
    nav.send_status_message("Flying to water source")
    nav.set_position(*SOURCE)

    nav.send_status_message("Descending to source")
    analysis.start()
    time.sleep(5)
    if len(bucket_avg[0]) > 0 and len(bucket_avg[1]) > 0:
       bucket_descent(big_bucket_height)
    else:
        time.sleep(5)
        bucket_descent(big_bucket_height)
    analysis.stop()
    nav.send_status_message("Stopped the analysis")

    nav.send_status_message("Filling up!")

    ActivatePump(10)

    nav.send_status_message("Flying to target")

    nav.set_altitude(20)

    nav.set_position(*TARGET_1)

    nav.send_status_message("Descending to target")
    analysis.start()
    clear_bucket_avg()    
    time.sleep(5)
    if len(bucket_avg[0]) > 0 and len(bucket_avg[1]) > 0:
       bucket_descent(big_bucket_height)
    else:
        time.sleep(5)
        bucket_descent(big_bucket_height)
    analysis.stop()
    nav.send_status_message("Stopped the analysis")

    nav.send_status_message("Filling up!")

    ActivatePump(10)
    clear_bucket_avg()    

    response = input("Next/end")
    if response.lower() == "next":
        pass
    else:
        break


nav.return_to_launch()
drone.close()
nav.send_status_message("Flight test script execution terminated")



