from src.modules.imaging.bucket_detector import BucketDetector
from src.modules.imaging.camera import DebugCamera
from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.analysis import ImageAnalysisDelegate


cam = DebugCamera("2813.jpg")
det = BucketDetector("samples/models/8n416.pt")
location = DebugLocationProvider()
analysis = ImageAnalysisDelegate(det, cam, location)

def test(arg, _):
    print(arg)

analysis.subscribe(test)

analysis.start()

