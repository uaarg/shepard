import time
import os
import threading

from dronekit import connect

from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.imaging.location import MAVLinkLocationProvider

CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14552

cam = RPiCamera()
#mavlink = MAVLinkDelegate()

drone = connect(CONN_STR, wait_read=False)

os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs)
os.makedirs(f"tmp/log/{ft_num}")  # no exist_ok bc. this folder should be new

i = 0
last_picture = time.time()

def location_dump_to(path: str):

    with open(path, 'w') as file:

        location = { "location" : str(drone.location.global_relative_frame) }
        
        json.dump(location, file)


def take_picture(_):
    global i
    global last_picture

    cam.caputure_to(f"tmp/log/{ft_num}/{i}.png")
    location_dump_to(f"tmp/log/{ft_num}/{i}.json")
    print(i)
    i += 1

def picture_loop(sleep):
    while True:
        take_picture(None)
        time.sleep(sleep)
thread_1 = threading.thread(picture_loop, 3)

thread_1.start()

#mavlink.run()

