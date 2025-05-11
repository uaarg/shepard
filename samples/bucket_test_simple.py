from src.modules.imaging.bucket_detector import BucketDetector
from src.modules.imaging.camera import DebugCameraFromDir, RPiCamera, DebugCamera
from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.analysis import ImageAnalysisDelegate

from ultralytics import YOLO
import os

import cv2
from PIL import Image
import time

cam = RPiCamera(0)
model_path = 'samples/models'
models = os.listdir(model_path)
models = ["best.pt"]
for file in models:
    model = YOLO(os.path.join(model_path, file))
    i = len(os.listdir("photos"))
    while True: 
        image = cam.capture()
        image.save(f"photos/{i}.png")
        results = model(image)

        result = results[0] # because one image
        a = result.plot()
        # b = Image.fromarray(a)
        # b.save(f"results/{i}.png")
        # 
        cv2.imshow(f'Result for model: {file}', a)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        time.sleep(0.5)
        i += 1
        # boxes = result.boxes

        # if boxes is not None and len(boxes) > 0:
        #     best_box = boxes[boxes.conf.argmax()]
        #     (x1, y1, x2, y2) = best_box.xyxy[0].tolist()  # box [x1, y1, x2, y2]
        #     conf = best_box.conf.item() # confidence threshold
        #     if conf < 0.5:
        #         print("not confident")
        #     else:
        #         print("confident")
        # else:
        #     print("no bounding box")

