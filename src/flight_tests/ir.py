from src.modules.imaging.detector import IrDetector
import time
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.location import DebugLocationProvider
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector
from PIL import Image, ImageDraw

def func(image: Image.Image, bb: BoundingBox):
    
        top_left_corner: Tuple[float, float] = (bb.position.x, bb.position.y)
        bottom_right_corner: Tuple[float, float] = (bb.position.x + bb.size.x,
                                                    bb.position.y + bb.size.y)

        draw = ImageDraw.Draw(image)
        draw.rectangle((top_left_corner, bottom_right_corner), outline="red", width=3)
        image.show()
        time.sleep(3)

camera = RPiCamera()
detector = IrDetector()
location = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(func)

analysis.start()


