from src.modules.autopilot import navigator
from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider

from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.detector import BalloonDetector
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.analysis import ImageAnalysisDebugger
from src.modules.imaging.location import DebugLocationProvider


detector = BalloonDetector()
location_debugger = DebugLocationProvider()
debugger = ImageAnalysisDebugger()
camera = RPiCamera()
analysis = ImageAnalysisDelegate(detector=detector, camera=camera , location_provider=location_debugger, debugger=debugger)




analysis.start()
