# Tests can be run with ./scripts/test.sh
# They will run all files in the test/ directory starting with 'test_'.
# Then, all functions starting with 'test_' will be run in that file. If the
# function raises an error, the test fails. Otherwise, the test passes.
# See test/test_camera.py for an example.

from typing import Optional

from PIL import Image

from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.camera import DebugCamera
from src.modules.imaging.debug import ImageAnalysisDebugger
from dep.labeller.benchmarks.detector import LandingPadDetector, BoundingBox
from dep.labeller.loader.label import Vec2


class DebugLandingPadDetector(LandingPadDetector):

    def __init__(self, vector: Optional[Vec2] = None, bb: Optional[BoundingBox] = None):
        self.vector = vector
        self.bounding_box = bb

    def predict(self, _image: Image.Image) -> BoundingBox:
        return self.bounding_box


def test_analysis_subscriber():
    camera = DebugCamera("res/test-image.jpeg")
    detector = DebugLandingPadDetector()
    analysis = ImageAnalysisDelegate(detector, camera)
    global detected
    detected = None

    # TODO: make this work?

    def _callback(_image, lon, lat):
        global detected
        detected = Vec2(lon, lat)

    analysis.subscribe(_callback)

    detector.vector = Vec2(0, 0)
    analysis._analyze_image()
    assert detected == detector.vector 
    old_vector = detected
    detector.vector = old_vector
    analysis._analyze_image()
    assert detected == detector.vector


class MockImageAnlaysisDebugger(ImageAnalysisDebugger):

    def __init__(self):
        self.image: Optional[Image.Image] = None
        self.bounding_box: Optional[BoundingBox] = None
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
    analysis = ImageAnalysisDelegate(detector, camera, debug)

    def run_analysis():
        detector.bounding_box = BoundingBox(Vec2(0, 0), Vec2(100, 100))
        analysis._analyze_image()
        assert debug.image is not None
        assert debug.bounding_box == detector.bounding_box

        detector.bounding_box = None
        analysis._analyze_image()
        assert debug.image is not None
        assert debug.bounding_box is None

    # ImageAnalysisDelegate will not hide the debugger
    debug.show()
    run_analysis()
    assert debug.is_visible

    # ImageAnalysisDelegate will not show the debugger
    debug.hide()
    run_analysis()
    assert not debug.is_visible
