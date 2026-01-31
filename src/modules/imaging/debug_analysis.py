from typing import Callable, Optional, List, Callable, Any

import threading
# from multiprocessing import Process
from .detector import BaseDetector, BoundingBox
from .camera import CameraProvider
from .debug import ImageAnalysisDebugger
from ..georeference.inference_georeference import get_object_location
from .location import LocationProvider
from PIL import Image, ImageDraw

import os

from .analysis import CameraAttributes, Inference


class DebugImageAnalysisDelegate:
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
                 detector: BaseDetector,
                 camera: CameraProvider,
                 location_provider: LocationProvider,
                 debugger: Optional[ImageAnalysisDebugger] = None,
                 ):
        import os
        self.detector = detector
        self.camera = camera
        self.debugger = debugger
        self.location_provider = location_provider
        self.subscribers: List[Callable[[Image.Image, float, float], Any]] = []
        self.camera_attributes = CameraAttributes()

        # log pictures taken
        os.makedirs("tmp/log", exist_ok=True)
        dirs = os.listdir("tmp/log")
        current_path = f"tmp/log/{len(dirs)}"
        os.makedirs(current_path)

        # path to store images taken during flight
        self.img_path = f"{current_path}/images"
        os.makedirs(self.img_path)

        # annotated bounding boxes
        self.bb_img_path = f"{current_path}/bb"
        os.makedirs(self.bb_img_path)

        # image number
        self.i = 0

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
        im.save(os.path.join(self.img_path, f"{self.i}.png"))

        bounding_box = self.detector.predict(im)

        if bounding_box:
            draw = ImageDraw.Draw(im)
            bb = (bounding_box.position.x, bounding_box.position.y,
                  bounding_box.size.x, bounding_box.size.y)
            draw.rectangle(bb)

        im.save(os.path.join(self.bb_img_path, f"{self.i}.png"))

        self.i += 1

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
