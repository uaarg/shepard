from typing import Callable, Optional

#import threading

from dep.labeller.benchmarks.detector import LandingPadDetector
from .camera import CameraProvider
from .debug import ImageAnalysisDebugger


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
                 detector: LandingPadDetector, camera: CameraProvider,
                 debugger: Optional[ImageAnalysisDebugger]):
        self.detector = detector
        self.camera = camera
        self.debugger = debugger
        self.subscribers = []

    def start(self):
        """
        Will start the image analysis process in another thread.
        """
        # Use `threading` to start `self._analysis_loop` in another thread.
        raise NotImplementedError()

    def _analysis_loop(self):
        """
        Actually preforms the image analysis indefinitely. This should be run
        in another thread; use `start()` to do so.
        """
        while True:
            # TODO:
            # Get image from camera
            # Run the landing pad detector
            # Update the ImageAnalysisDebugger if present/enabled
            # Call all subscribed callbacks (see subscribe)
            pass

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

