from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.camera import DebugCamera
from src.modules.imaging.detector import ArucoDetector
from src.modules.imaging.analysis import ImageAnalysisDelegate

def print_when_found(image, bounding_box):
    print(bounding_box[0])

camera = DebugCamera(dummy_image_path="tmp/aruco_mark_0.png")
detector = ArucoDetector()
location = DebugLocationProvider()

analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(print_when_found)

analysis.start()

print("Starting analysis")
