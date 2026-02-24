from PIL import Image
from src.modules.emu import Emu
import time
import json
import threading

from src.modules.imaging.camera import DepthCapture, OakdCamera

emu = Emu("tmp")
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
    global latest_capture, i

    msg = json.loads(message)

    if msg["type"] == "image" and msg["message"] == "capture":
        print("sending image")
        latest_capture = camera.capture_with_depth()
        im = Image.fromarray(latest_capture.rgb)

        im.save(f"./tmp/{i}.jpeg")
        emu.send_image(f"{i}.jpeg")

        i += 1


def measure(message):
    global latest_capture

    msg = json.loads(message)

    if msg["type"] == "getDistance":
        print("getting distance")
        points = msg["message"]

        p1 = points["p1"]
        p2 = points["p2"]

        if latest_capture is not None:
            distance = latest_capture.distance_between_points(p1["x"], p1["y"], p2["x"], p2["y"])
            send = {
                "type": "distance",
                "message": distance
            }
            emu.send_msg(json.dumps(send))
            print(f"distance sent: {send}")


emu.subscribe(send_img)
emu.subscribe(measure)
time.sleep(500)
