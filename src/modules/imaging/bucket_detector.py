from typing import Optional

from PIL import Image
import numpy as np
import cv2

from dep.labeller.loader import Vec2
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector

from ultralytics import YOLO

class BucketDetector(LandingPadDetector):
    
    def __init__(self, model_path):
        print(f"model: {model_path}")
        self.model = YOLO(model_path)

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        results = self.model(image)

        result = results[0] # because one image

        boxes = result.boxes

        if boxes is not None and len(boxes) > 0:
            best_box = boxes[boxes.conf.argmax()]
            (x1, y1, x2, y2) = best_box.xyxy[0].tolist()  # box [x1, y1, x2, y2]
            conf = best_box.conf.item() # confidence threshold
            if conf < 0.5:
                return None
            else:
                return BoundingBox(Vec2(x1, y1), Vec2(x2 - x1, y2 - y1))
        else:
            return None

