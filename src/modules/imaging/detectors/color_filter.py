from typing import Optional

from PIL import Image
import numpy as np
import cv2

from src.modules.imaging.detector import BoundingBox, Detector, Vec2


class ColorFilterDetector(Detector):

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        img = np.array(image)
        gray_img = img[:, :, 2]

        _, thresh_img = cv2.threshold(gray_img, 240, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        min_box = None
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if min_box is None or (w + x) < min_box[0] + min_box[2]:
                min_box = [x, y, w, h]

        if not min_box:
            return None

        x, y, w, h = min_box[:4]

        return BoundingBox(Vec2(x, y), Vec2(w, h))
