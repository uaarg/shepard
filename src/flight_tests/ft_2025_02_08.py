import time
import os
from PIL import Image

from src.modules.imaging.camera import RPiCamera
from dep.labeller.benchmarks.yolov10 import YoloDetector
#from src.modules.imaging.mavlink import MAVLinkDelegate
#from src.modules.imaging.location import MAVLinkLocationProvider

cam = RPiCamera()
model = YoloDetector()
#mavlink = MAVLinkDelegate()
#location = MAVLinkLocationProvider(mavlink)

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
    if now - last_picture < 5:
        return
    last_picture = now

    cam.caputure_to(f"tmp/log/{ft_num}/{i}.png")
    #location.dump_to(f"tmp/log/{ft_num}/{i}.json")
    print(i)
    i += 1
    return (f"tmp/log/{ft_num}/{i}.png")


def predict(pathToImage: str):
    image = Image.open(pathToImage)
    results = model.predict(image)
    with open('tmp/2025_02_08.log', 'w') as file:
        file.write(results)
    print(results)


while True:
    predict(take_picture(None))
    time.sleep(5)

#mavlink.subscribe(take_picture)
#mavlink.run()

