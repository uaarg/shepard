import time
import os
from PIL import Image, ImageDraw
import numpy as np
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
    #if now - last_picture < 5:
     #   return
    last_picture = now
    path = f"tmp/log/{ft_num}/{i}.png"
    cam.caputure_to(path)
    #location.dump_to(f"tmp/log/{ft_num}/{i}.json")
    print(i)
    i += 1
    return path 


def predict(pathToImage: str):
    image = Image.open(pathToImage)
    results = model.predict(image)
    draw_bbox(image, results)
    with open('tmp/2025_02_08.log', 'w') as file:
        file.write(str(results))
    print(results)

def draw_bbox(image: Image.Image, results: dict):
    
    draw = ImageDraw.Draw(image)
    
    for result in results:
        x1 = result['x'] - result['w'] // 2
        y1 = result['y'] - result['h'] // 2
        x2 = result['x'] + result['w'] // 2
        y2 = result['y'] + result['h'] // 2

        draw.rectangle([x1, y1, x2, y2], outline='red', width=3)

    image.show()

while True:
    predict(take_picture(None))
    time.sleep(1)

#mavlink.subscribe(take_picture)
#mavlink.run()

