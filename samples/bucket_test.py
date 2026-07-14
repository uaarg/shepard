from src.modules.imaging.bucket_detector import BucketDetector
from src.modules.imaging.camera import DebugCameraFromDir
from src.modules.imaging.debug_analysis import DebugImageAnalysisDelegate

import time

cam = DebugCameraFromDir("images")
det = BucketDetector("samples/models/n640.pt")
analysis = DebugImageAnalysisDelegate(det, cam)


def test(a1=None, a2=None):
    if a1 is not None and a2 is not None:
        print(a1)
        print(a2)


analysis.subscribe(test)
analysis.start()

# let analysis run for 1 second
time.sleep(1)
analysis.stop()
