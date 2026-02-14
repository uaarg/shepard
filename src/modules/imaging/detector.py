from typing import Optional

from PIL import Image
import numpy as np
import cv2
from cv2 import aruco

from dep.labeller.loader import Vec2
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector



class IrDetector(LandingPadDetector):

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        img = np.array(image)

        gray_img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        max_val = np.max(gray_img) # returns maximum value of brightness 
        if max_val < 200: return None #lower threshold for intensity 
        _, thresh = cv2.threshold(gray_img, max_val - 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # cv2.drawContours(thresh, contours, -1, (0, 255, 0), 2)

        if len(contours) == 0: return None

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

        return BoundingBox(Vec2(x, y), Vec2(w, h))


class ArucoDetector():

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        img  = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)

        params = cv2.aruco.DetectorParemeters()

        corners, ids, rejected = cv2.aruco.detectMarkers(img, aruco_dict, parameters=params)
        
        if ids:
            for c in zip(corners, ids):
                
                pts = c[0]

                x_min = pts[:, 0].min()
                x_max = pts[:, 0].max()
                y_min = pts[:, 1].min()
                y_max = pts[:, 1].max()

                x = (x_min + x_max) / 2
                y = (y_min + y_max) / 2
                w = (x_max - x_min)
                h = (y_max - y_min)
         
                return BoundingBox(Vec2(x, y), Vec2(w, h))

