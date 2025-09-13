from src.modules.imaging import analysis
from src.modules.imaging import camera
from src.modules.imaging import debug
from src.modules.imaging import location
from dep.labeller.benchmarks import yolo

mavlink_delegate = location.MAVLinkDelegate()
location_provider = location.MAVLinkLocationProvider(mavlink_delegate)
location_provider = location.DebugLocationProvider()
location_provider.debug_change_location(altitude=1)

detector = yolo.YoloDetector(weights="landing_nano.pt")
cam = camera.RPiCamera()
debugger = debug.ImageAnalysisDebugger()
debugger = None
img_analysis = analysis.ImageAnalysisDelegate(detector, cam, location_provider,
                                              debugger)

#img_analysis.subscribe(lambda _, __, ___: debugger.show())
img_analysis.subscribe(lambda _, lon, lat: print(lon, lat))
img_analysis.start()

mavlink_delegate.run()
