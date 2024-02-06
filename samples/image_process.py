# This can be run with `samples/run.sh image_process.py`
# Or, if you don't have bash installed, run the equivalent of:
#    PYTHONPATH=".:dep/labeller" python3 samples/image_process.py

import time

from src.modules import imaging
from dep.labeller.benchmarks.colorfilter import ColorFilterDetector

detector = ColorFilterDetector()
camera = imaging.camera.DebugCamera("./res/test-image.jpeg")
debugger = imaging.debug.ImageAnalysisDebugger()
analysis = imaging.analysis.ImageAnalysisDelegate(detector, camera, debugger)

analysis.subscribe(print)  # Will print all results to stdout
analysis.start()

print("Analysis is running in the background.")
print("This should have printed very soon after the program started.")

while True:
    # Dummy loop. In a real scenario, we would be running autopilot control
    # code here.
    time.sleep(100)
