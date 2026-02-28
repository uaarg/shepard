# Tests can be run with ./scripts/test.sh
# They will run all files in the test/ directory starting with 'test_'.
# Then, all functions starting with 'test_' will be run in that file. If the
# function raises an error, the test fails. Otherwise, the test passes.
# See test/test_camera.py for an example.

from typing import Optional

from PIL import Image

from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import DebugCamera
from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.debug import ImageAnalysisDebugger
from src.modules.imaging.detector import BaseDetector, BoundingBox, Vec2


class DebugDetector(BaseDetector):

    def __init__(self,
                 vector: Optional[Vec2] = None,
                 bb: Optional[BoundingBox] = None):
        self.bounding_box = bb

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        return self.bounding_box


def test_analysis_subscriber():
    camera = DebugCamera("res/test-image.jpeg")
    detector = DebugDetector()
    location_provider = DebugLocationProvider()
    location_provider.set_altitude(1.0)
    analysis = ImageAnalysisDelegate(detector, camera, location_provider)

    global detected
    detected = None

    def _callback(_image, lon_lat):
        global detected

        detected = None
        if lon_lat:
            detected = Vec2(lon_lat[0], lon_lat[1])

    analysis.subscribe(_callback)

    detector.bounding_box = None
    analysis._analyze_image()
    assert detected is None
    detector.bounding_box = BoundingBox(Vec2(20, 20), Vec2(50, 50))
    analysis._analyze_image()
    assert detected is not None
    result = detected - Vec2(-115.48873916832288, 5.483286467459389e-06)
    assert result.norm < 0.01


class MockImageAnlaysisDebugger(ImageAnalysisDebugger):

    def __init__(self):
        self.image: Image.Image | None = None
        self.bounding_box: BoundingBox | None = None
        self.is_visible = False

    def show(self):
        #if not self.image:
        #raise RuntimeError("No image set. Cannot show without an image")
        self.is_visible = True

    def hide(self):
        self.is_visible = False

    def visible(self) -> bool:
        return self.is_visible

    def set_image(self, image: Image.Image):
        self.image = image.copy()

    def set_bounding_box(self, bb: BoundingBox):
        if not self.image:
            return  # return no image set error

        self.bounding_box = bb


def test_analysis_debugger():
    camera = DebugCamera("res/test-image.jpeg")
    detector = DebugLandingPadDetector()
    debug = MockImageAnlaysisDebugger()
    location_provider = DebugLocationProvider()
    location_provider.set_altitude(1.0)
    analysis = ImageAnalysisDelegate(detector, camera, location_provider,
                                     debug)

    def run_analysis():
        detector.bounding_box = BoundingBox(Vec2(0, 0), Vec2(100, 100))
        analysis._analyze_image()
        assert debug.image is not None
        assert debug.bounding_box == detector.bounding_box

        detector.bounding_box = None
        analysis._analyze_image()
        assert debug.image is not None

    # ImageAnalysisDelegate will not hide the debugger
    debug.show()
    run_analysis()
    assert debug.is_visible

    # ImageAnalysisDelegate will not show the debugger
    debug.hide()
    run_analysis()
    assert not debug.is_visible
