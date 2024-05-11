from typing import Callable, Optional, List, Callable, Any

import threading
from dep.labeller.benchmarks.detector import LandingPadDetector, BoundingBox
from .camera import CameraProvider
from .debug import ImageAnalysisDebugger
from ..georeference.inference_georeference import get_object_location
from .location import LocationProvider
from PIL import Image


class CameraAttributes:

    def __init__(self):
        self.focal_length = 0.01
        self.angle = 10 / 180 * 3.14159  # in radians
        self.resolution = (640, 640)


class Inference:

    def __init__(self, bounding_box: BoundingBox, relative_alt):
        camera_attributes = CameraAttributes()
        position = bounding_box.position
        size = bounding_box.size
        self.x = (position.x + size.x / 2) / camera_attributes.resolution[0]
        self.y = (position.y + size.y / 2) / camera_attributes.resolution[1]
        self.relative_alt = relative_alt


class ImageAnalysisDelegate:
    """
    Implements an imaging inference loops and provides several methods which
    can be used to query the latest image analysis results.

    Responsible for capturing pictures regularly, detecting any landing pads in
    those pictures and then providing the most recent estimate of the landing
    pad location from the camera's perspective.

    Pass an `ImageAnalysisDebugger` when constructing to see a window with live
    results.

    TODO: geolocate the landing pad using the drone's location.
    """

    def __init__(self,
                 detector: LandingPadDetector,
                 camera: CameraProvider,
                 location_provider: LocationProvider,
                 debugger: Optional[ImageAnalysisDebugger] = None):
        self.detector = detector
        self.camera = camera
        self.debugger = debugger
        self.location_provider = location_provider
        self.subscribers: List[Callable[[Image.Image, float, float], Any]] = []
        self.camera_attributes = CameraAttributes()

    def get_inference(self, bounding_box: BoundingBox) -> Optional[Inference]:
        inference = Inference(bounding_box, self.location_provider.altitude())
        if inference.x > 1 or inference.y > 1:
            print("Bounding Box out of bounds")
            return None
        return inference

    def start(self):
        """
        Will start the image analysis process in another thread.
        """
        thread = threading.Thread(target=self._analysis_loop)
        thread.start()
        # Use `threading` to start `self._analysis_loop` in another thread.

    def _analyze_image(self):
        """
        Actually performs the image analysis once. Only useful for testing,
        should otherwise we run by `start()` which then starts
        `_analysis_loop()` in another thread.
        """
        im = self.camera.capture()
        bounding_box = self.detector.predict(im)
        print(self.debugger)
        if self.debugger is not None:
            self.debugger.set_image(im)
            if bounding_box is not None:
                self.debugger.set_bounding_box(bounding_box)
        for subscribers in self.subscribers:
            if bounding_box:
                inference = self.get_inference(bounding_box)
                if inference:
                    lon, lat = get_object_location(self.camera_attributes,
                                                   inference)
                    subscribers(im, lon, lat)
        # Get image from camera
        # Run the landing pad detector
        # Update the ImageAnalysisDebugger if present/enabled
        # Call all subscribed callbacks (see subscribe)

    def _analysis_loop(self):
        """
        Indefinitely run image analysis. This should be run in another thread;
        use `start()` to do so.
        """
        while True:
            self._analyze_image()

    def subscribe(self, callback: Callable):
        """
        Subscribe to image analysis updates. For example:

            def myhandler(image: Image.Image, bounding_box: BoundingBox):
                if bounding_box is None:
                    print("No bounding box detected")
                else:
                    print("Bounding box detected")

            imaging_process.subscribe(myhandler)
        """
        self.subscribers.append(callback)
