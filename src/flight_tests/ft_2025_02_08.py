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


def predict(pathToImage: str)
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















Last login: Fri Feb  7 01:40:43 on ttys004
❯ cd Desktop
❯ clear
import PIL.Image
import PIL.Image
import numpy as np
from ultralytics import YOLO
from PIL import Image
model = YOLO("yolov10n.pt")
import copy

# Perform object detection on an image




image = np.array(Image.open('catandsuitcase2.jpg').convert("RGB"))



results = model(image) # This prints two lines


class_names = model.names  # Dictionary mapping class IDs to object names

detected_objects = []  # List to store results

for result in results:
    if hasattr(result, "boxes") and result.boxes is not None:
        class_ids = result.boxes.cls.cpu().numpy()  # Get class IDs
        boxes = result.boxes.xyxy.cpu().numpy()  # Get bounding box coordinates

        # Create a list of tuples (object_name, bounding_box)

        detected_objects = [
            (class_names[int(cls_id)], box.tolist())
            for cls_id, box in zip(class_ids, boxes)
        ]


result_dict = {}

for obj_name, bbox in detected_objects:
    print(f"Detected: {obj_name}, BBox: {bbox}")

    result_dict[obj_name] = copy.deepcopy(result_dict[obj_name] + [bbox]) if (obj_name in result_dict) else [bbox]


print(result_dict)
