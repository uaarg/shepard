from src.modules.imaging.bucket_detector import BucketDetector
from src.modules.imaging.camera import DebugCameraFromDir
from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.analysis import ImageAnalysisDelegate


cam = DebugCameraFromDir("images")
det = BucketDetector("samples/models/11n640.pt")
location = DebugLocationProvider()
analysis = ImageAnalysisDelegate(det, cam, location)

def test(a1, a2):
    if a1 != None and a2 != None:
        print(a1)
        print(a2)

analysis.subscribe(test)

analysis.start()

