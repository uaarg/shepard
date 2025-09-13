from src.modules.imaging.detector import IrDetector
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.location import DebugLocationProvider


camera = RPiCamera()
detector = IrDetector()
location = DebugLocationProvider()


def test(img, _):
    print("Image taken")



analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(test)

analysis.start()
