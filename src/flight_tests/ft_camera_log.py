import time
import os
import threading

from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.imaging.location import MAVLinkLocationProvider

cam = RPiCamera()
mavlink = MAVLinkDelegate()
location = MAVLinkLocationProvider(mavlink)

os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs)
os.makedirs(f"tmp/log/{ft_num}")  # no exist_ok bc. this folder should be new

i = 0
last_picture = time.time()


def take_picture(_):
    global i
    global last_picture

    now = time.time()
    if now - last_picture < 1 / 15:
        return
    last_picture = now

    cam.caputure_to(f"tmp/log/{ft_num}/{i}.png")
    location.dump_to(f"tmp/log/{ft_num}/{i}.json")
    print(i)
    i += 1

def picture_loop(sleep):
    while True:
        take_picture(None)
        time.sleep(sleep)
thread_1 = threading.thread(picture_loop, 3)

thread_1.start()

mavlink.run()

