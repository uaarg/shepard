from src.modules.imaging import analysis
from src.modules.imaging import camera
from src.modules.imaging import debug
from dep.labeller.benchmarks import yolo

detector = yolo.YoloDetector(weights="landing_nano.pt")
cam = camera.RPiCamera()
debugger = debug.ImageAnalysisDebugger()
img_analysis = analysis.ImageAnalysisDelegate(detector, cam, debugger)

img_analysis.subscribe(lambda _, __, ___: debugger.show())
img_analysis.subscribe(lambda _, lon, lat: print(lon, lat))
img_analysis._analysis_loop()
