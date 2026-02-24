from typing import Optional

from PIL import Image

from .detector import Vec2, BoundingBox, BaseDetector

from ultralytics import YOLO


class BucketDetector(BaseDetector):

    def __init__(self, model_path):
        print(f"model: {model_path}")
        self.model = YOLO(model_path)

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        results = self.model(image, verbose = False)

        result = results[0]  # because one image

        boxes = result.boxes

        if boxes is not None and len(boxes) > 0:
            best_box = boxes[boxes.conf.argmax()]
            (x1, y1, x2, y2) = best_box.xyxy[0].tolist()  # box [x1, y1, x2, y2]
            conf = best_box.conf.item()  # confidence threshold
            if conf < 0.75:
                return None
            else:
                return BoundingBox(Vec2(x1, y1), Vec2(x2, y2))
        else:
            return None
