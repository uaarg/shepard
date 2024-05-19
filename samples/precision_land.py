from src.modules.autopilot import precision_landing


from src.modules import imaging
from dep.labeller.benchmarks.colorfilter import ColorFilterDetector

landing_pad = (0.762, 0.762)

detector = ColorFilterDetector()
camera = imaging.camera.WebcamCamera()
debugger = imaging.debug.ImageAnalysisDebugger()
analysis = imaging.analysis.ImageAnalysisDelegate(detector, camera, debugger)
landing = precision_landing.PrecisionLanding(None, landing_pad)

analysis.subscribe(landing.send)
analysis.start()