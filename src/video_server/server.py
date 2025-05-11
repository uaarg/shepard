from http.server import HTTPServer, SimpleHTTPRequestHandler 
import os

from src.modules.imaging.camera import RPiCamera

import RPi.GPIO as GPIO

from src.modules.autopilot import navigator
from dronekit import connect

CONN_STR = "tcp:127.0.0.1:14650"
MESSENGER_PORT = 14550

drone = connect(CONN_STR, wait_ready=False)

nav = navigator.Navigator(drone, MESSENGER_PORT)

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

        if self.path == '/left':
            self.send_response(200)
            self.end_headers()
            nav.set_position_relative(0, -STEP_SIZE)

        elif self.path == '/right':
            self.send_response(200)
            self.end_headers()
            nav.set_position_relative(0, STEP_SIZE)

        elif self.path == '/up':
            self.send_response(200)
            self.end_headers()            
            nav.set_position_relative(STEP_SIZE, 0)

        elif self.path == '/down':
            self.send_response(200)
            self.end_headers()
            nav.set_position_relative(-STEP_SIZE, 0)

        elif self.path == '/ascend':
            self.send_response(200)
            self.end_headers()
            nav.set_altitude_relative(STEP_SIZE)

        elif self.path == '/descend':
            self.send_response(200)
            self.end_headers()
            nav.set_altitude_relative(-STEP_SIZE)

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
        self.server = HTTPServer(('', self.port), MyHandler) # Empty string means localhost
        print(f"Server running on http://localhost:{self.port}")
        self.server.serve_forever()

if __name__ == "__main__":
    IMG_DIR = "tmp/current_img.webp"

    # set up GPIO for bucket
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_PIN, GPIO.OUT)
    GPIO.output(23, GPIO.LOW)


    # make sure directory exists
    os.makedirs("video_server/tmp/", exist_ok=True)
    
    cam = RPiCamera(0)


    # start the webserver
    server = WebServer(8081)
    server.run()
