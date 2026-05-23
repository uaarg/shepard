from PIL import Image
from src.modules.emu import Emu
import time
import json
import os

from src.modules.imaging.camera import RPiCamera, DebugCamera

os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs) + 1
os.makedirs(f"tmp/log/{ft_num}")  # no exist_ok bc. this folder should be new

emu = Emu("tmp/log")
i = 0

def print_conn():
    print("connecton made")

emu.set_on_connect(print_conn)

emu.start_comms()
time.sleep(2)

camera = DebugCamera("res/test-image.jpeg")


def send_img(message):
    global i, ft_num

    msg = json.loads(message)

    if msg["type"] == "image" and msg["message"] == "capture":
        print("sending image")
        im = camera.capture()
        im.save(f"tmp/log/{ft_num}/{i}.jpeg")
        emu.send_image(f"{ft_num}/{i}.jpeg")

        i += 1

emu.subscribe(send_img)

while True:
    time.sleep(500)
