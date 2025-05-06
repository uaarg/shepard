from src.modules.imaging.detector import IrDetector

camera = RPiCamera()
detector = IrDetector()
location = DebugLocationProvider()


def test(img):
    print("Image taken")



analysis = ImageAnalysisDelegate(detector, camera, location)
analysis.subscribe(test)


analyis.run()
