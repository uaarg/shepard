from typing import Tuple
import time
import os
from PIL import Image, ImageDraw

from dep.labeller.benchmarks.detector import BoundingBox
from dep.labeller.benchmarks.quick_hough import QuickHoughDetector
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.camera import DebugCamera



location_provider = DebugLocationProvider()
camera = DebugCamera("20/0.png")
detector = QuickHoughDetector()

   
analysis_delegate = ImageAnalysisDelegate(detector=detector, 
                                          camera=camera, 
                                          location_provider=location_provider) 


def debug(img: Image.Image, bb: BoundingBox):

        top_left_corner: Tuple[float, float] = (bb.position.x, bb.position.y)
        bottom_right_corner: Tuple[float, float] = (bb.position.x + bb.size.x,
                                                    bb.position.y + bb.size.y)

        draw = ImageDraw.Draw(img)
        draw.rectangle((top_left_corner, bottom_right_corner))

analysis_delegate.subscribe(debug)
analysis_delegate.start()

for pic in os.listdir("20"):

        camera.set_image("20/"+pic)
        time.sleep(2)
