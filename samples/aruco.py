from src.modules.imaging.camera import OakdCamera
from src.modules.imaging.analysis import ImageAnalysisDelegate
import threading
from PIL import Image
import time

from src.modules.imaging.detector import ArucoDetector, BoundingBox


def method(im: Image.Image, bb: BoundingBox):
    print(bb)

detector = ArucoDetector()

camera = OakdCamera()
camera_thread = threading.Thread(target=camera.start(), daemon=True)
camera_thread.start()
time.sleep(5)

analysis_delegate = ImageAnalysisDelegate(detector=detector, camera=camera)
analysis_delegate.subscribe(method)
analysis_delegate.start()
