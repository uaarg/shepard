from typing import Optional

from PIL import Image
import numpy as np
import cv2

from dep.labeller.loader import Vec2
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector



class IrDetector(LandingPadDetector):

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        img = np.array(image)

        gray_img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        max_val = np.max(gray_img) # returns maximum value of brightness 
        _, thresh = cv2.threshold(gray_img, max_val - 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # cv2.drawContours(thresh, contours, -1, (0, 255, 0), 2)
        cv2.imwrite("res.png", thresh)

        if len(contours) == 0: return None

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

        return BoundingBox(Vec2(x, y), Vec2(w, h))



        
        

