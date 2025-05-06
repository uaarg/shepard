from typing import Callable, Optional, List, Callable, Any, Tuple

import time
import threading
from PIL import Image
import numpy as np
# from multiprocessing import Process

from dep.labeller.benchmarks.detector import LandingPadDetector, BoundingBox
from src.modules.imaging.camera import CameraProvider
from src.modules.imaging.debug import ImageAnalysisDebugger
from src.modules.georeference.inference_georeference import get_object_location
from src.modules.imaging.location import LocationProvider


class CameraAttributes:

    def __init__(self):
        self.focal_length = 0.0034
        self.angle = 0  # in radians
        self.resolution = (1920, 1080)


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
                 debugger: Optional[ImageAnalysisDebugger] = None,
                 ):
        self.detector = detector
        self.camera = camera
        self.debugger = debugger
        self.location_provider = location_provider
        self.subscribers: List[Callable[[Image.Image, float, float], Any]] = []
        self.camera_attributes = CameraAttributes()

    def get_inference(self, bounding_box: BoundingBox) -> Inference:
        inference = Inference(bounding_box, self.location_provider.altitude())
        return inference


    def start(self):
        """
        Will start the image analysis process in another thread.
        """
        thread = threading.Thread(target=self._analysis_loop)
        # process = Process(target=self._analysis_loop)
        thread.start()
        # process.start()
        # Use `threading` to start `self._analysis_loop` in another thread.


    def _analyze_image(self):
        """
        Actually performs the image analysis once. Only useful for testing,
        should otherwise we run by `start()` which then starts
        `_analysis_loop()` in another thread.
        """
        im = self.camera.capture()
        bounding_box = self.detector.predict(im)
        if self.debugger is not None:
            self.debugger.set_image(im)
            if bounding_box is not None:
                self.debugger.set_bounding_box(bounding_box)

        for subscriber in self.subscribers:
            if bounding_box:
                inference = self.get_inference(bounding_box)
                if inference:
                    x, y = get_object_location(self.camera_attributes,
                                                   inference)
                    subscriber(im, (x, y))
            else:
                subscriber(im, None)

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


class DebugImageAnalysisDelegate(ImageAnalysisDelegate):
    """
    Like ImageAnalysisDelegate, but provides a randomized location prediction
    about self.x, self.y with standard deviation of self.std.

    This can be used to simulate real input and a system's ability to withstand
    noise/error from image analysis.

    If the camera provider is None, the image argument in the callback will be
    None. This may break some existing analysis subscribers/callbacks.

    Example Usage:

        camera = DebugCameraProvider()  # [OPTIONAL] Produces an image in the callback, can be None
        analysis = ImageAnalysisDelegate(camera, delay=2.0)  # Produce a result every 2s

        # Set center from which to produce noisy estimates from
        analysis.x = 42
        analysis.y = 100

        # Set standard deviation
        analysis.std = 0.8

        # Start the analysis thread, listen with my_callback
        analysis.subscribe(my_callback)
        analysis.start()
    """

    def __init__(self, camera: CameraProvider, delay: float = 1.0):
        super().__init__(None, camera, None, None)
        self.x = 0
        self.y = 0
        self.std = 1
        self.delay = delay

    def rand_xy(self) -> Tuple[float, float]:
        """
        Generate a random (x, y) point following a normal distribution about
        (self.x, self.y) with standard deviation self.std.
        """
        x = np.random.normal(loc=self.x, scale=self.std)
        y = np.random.normal(loc=self.y, scale=self.std)
        return x, y

    def _analyze_image(self):
        time.sleep(self.delay)

        im = self.camera.capture() if self.camera is not None else None
        for subscriber in self.subscribers:
            subscriber(im, self.rand_xy())
