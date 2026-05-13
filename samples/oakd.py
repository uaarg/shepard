from PIL import Image
from src.modules.emu import Emu
import time
import json
import threading
import numpy as np
import os

from src.modules.imaging.camera import DepthCapture, OakdCamera

os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs) + 1
os.makedirs(f"tmp/log/{ft_num}")  # no exist_ok bc. this folder should be new

emu = Emu("tmp/log")
i = 0

def print_conn():
    print("connecton made")

emu.set_on_connect(print_conn)
latest_capture: DepthCapture | None = None

emu.start_comms()
time.sleep(2)

camera = OakdCamera()


camera_thread = threading.Thread(target=camera.start(), daemon=True)
camera_thread.start()

def send_img(message):
    global latest_capture, i, ft_num

    msg = json.loads(message)

    if msg["type"] == "image" and msg["message"] == "capture":
        print("sending image")
        latest_capture = camera.capture_with_depth()
        im = Image.fromarray(latest_capture.rgb)
        depth_map = latest_capture.point_cloud

        im.save(f"tmp/log/{ft_num}/{i}.jpeg")
        np.save(f"tmp/log/{ft_num}/{i}.npy", depth_map)
        emu.send_image(f"{ft_num}/{i}.jpeg")

        i += 1

def measure(message):
    global latest_capture

    msg = json.loads(message)

    if msg["type"] == "getPoint":
        print("getting point")
        point = msg["message"]["pixel"]
        requestId = msg["requestId"]

        if latest_capture is not None:
            print(f"pixel: {point['x']}, {point['y']}")
            distPoint = latest_capture.get_point(point["x"], point["y"])
            send = {
                "requestId": requestId,
                "type": "point", 
                "message": {
                    "x": distPoint[0],
                    "y": distPoint[1],
                    "z": distPoint[2]
                    }
            }

            # If point is (0,0,0), measurement is invalid
            if (not np.any(distPoint)):
                send["message"] = "invalid"

            emu.send_msg(json.dumps(send))
            print(f"distance sent: {send}")


emu.subscribe(send_img)
emu.subscribe(measure)
time.sleep(500)
