from http.server import HTTPServer, SimpleHTTPRequestHandler 
import os

from pymavlink import mavutil

from src.modules.imaging.camera import RPiCamera

import RPi.GPIO as GPIO

from src.modules.autopilot import navigator
from dronekit import connect

CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14550

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)
nav.POSITION_TOLERANCE = 0.1
STEP_SIZE = 0.1

GPIO_PIN = 23


class MyHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # If the request is for the root, serve index.html
        if self.path == '/':
            self.path = 'src/video_server/index.html'
        else:
            img = cam.capture()
            # img.resize((960, 540))
            img.resize((480, 270))
            img.save(IMG_DIR)

        print(self.path)

        return super().do_GET()
    
    def do_POST(self):
        print('POST', self.path)
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

class WebServer:

    def __init__(self, port):

        self.port = port
        self.server = None
    
    def run(self):

        #setup server
        self.server = HTTPServer(('0.0.0.0', self.port), MyHandler) # Empty string means localhost
        print(f"Server running on http://localhost:{self.port}")
        self.server.serve_forever()

if __name__ == "__main__":
    IMG_DIR = "tmp/video_server/current_img.webp"

    # set up GPIO for bucket
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    GPIO.output(23, GPIO.LOW)


    # make sure directory exists
    os.makedirs("tmp/video_server/", exist_ok=True)
    
    cam = RPiCamera(1)
    # cam = WebcamCamera()


    # start the webserver
    server = WebServer(8081)
    server.run()
