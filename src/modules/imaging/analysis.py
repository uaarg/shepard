from abc import abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional, List, Callable, Any, Tuple

import threading
# from multiprocessing import Process
from dep.labeller.benchmarks.detector import LandingPadDetector, BoundingBox
from .camera import CameraProvider
from .debug import ImageAnalysisDebugger
from ..georeference.inference_georeference import get_object_location
from .location import LocationProvider
from ..autopilot.navigator import Navigator
from PIL import Image
import os


class CameraAttributes:
    def __init__(self):
        self.focal_length = 0.0034
        self.angle = 0  # in radians
        self.resolution = (1920, 1080)


class ImagingInference:
    def __init__(self, bounding_box: BoundingBox, relative_alt):
        camera_attributes = CameraAttributes()
        position = bounding_box.position
        size = bounding_box.size
        self.x = (position.x + size.x / 2) / camera_attributes.resolution[0]
        self.y = (position.y + size.y / 2) / camera_attributes.resolution[1]
        self.relative_alt = relative_alt

@dataclass
class AnalysisResult:
    """
    Represents the result of an analysis performed by an `AnalysisDelegate`.

    This data class stores the relative position of the detected target
    with respect to the drone's current location and orientation.

    Attributes:
        front (float): The forward offset of the target in meters.
            Positive values indicate the target is ahead of the drone,
            negative values indicate it is behind.
        left (float): The lateral offset of the target in meters.
            Positive values indicate the target is to the right of the drone,
            negative values indicate it is to the left.
    """
    front: float
    right: float

class AnalysisDelegate:

    def __init__(self) -> None:
        self.thread: threading.Thread
        self.loop = False
        self.subscribers: List[Callable[[AnalysisResult], None]] = []

    @abstractmethod
    def _analyze_unit(self):
        """Analyse and subscribe the result of analysis to subscribers"""
        raise NotImplementedError

    def start(self):
        """
        Will start the analysis process in another thread.
        """
        if self.loop is False:
            self.loop = True
            self.thread = threading.Thread(target=self._analysis_loop)
            self.thread.start()

    def stop(self):
        self.loop = False
        assert self.thread is not None
        self.thread.join()

    def _analysis_loop(self):
        """
        Indefinitely run analysis. This should be run in another thread;
        use `start()` to do so.
        """
        while self.loop:
            try:
                self._analyze_unit()
            except Exception as e:
                print("Error in analysis loop: ", e)
                self.loop = False

    def subscriberService(self, analysis_result: AnalysisResult):
        """Service function that subscribes the reult to every subscriber"""
        for subscriber in self.subscribers:
            subscriber(analysis_result)

    def subscribe(self, callback: Callable[[AnalysisResult], None]):
        """
        Subscribe to analysis updates. For example:

            def myhandler(image: Image.Image, bounding_box: BoundingBox):
                if bounding_box is None:
                    print("No bounding box detected")
                else:
                    print("Bounding box detected")

            imaging_process.subscribe(myhandler)
        """
        self.subscribers.append(callback)

class ImageAnalysisDelegate(AnalysisDelegate):
    """
    Implements an imaging inference loops and provides several methods which
    can be used to query the latest image analysis results.

    Responsible for capturing pictures regularly, detecting any landing pads in
    those pictures and then providing the most recent estimate of the landing
    pad location from the camera's perspective.

    Pass an `ImageAnalysisDebugger` when constructing to see a window with live
    results.
    """

    def __init__(self,
                 detector: LandingPadDetector,
                 camera: CameraProvider,
                 location_provider: Optional[LocationProvider] = None,
                 navigation_provider: Optional[Navigator] = None,
                 debugger: Optional[ImageAnalysisDebugger] = None):
        self.detector = detector
        self.camera = camera
        self.debugger = debugger
        
        if location_provider is None and navigation_provider is None:
            raise ValueError("Either location_provider or navigation_provider must be provided.")

        self.location_provider = location_provider
        self.navigation_provider = navigation_provider
        
        self.camera_attributes = CameraAttributes()

        super().__init__()

    def get_inference(self, bounding_box: BoundingBox) -> ImagingInference:
        if self.location_provider is not None:
            altitude = self.location_provider.altitude()
        elif self.navigation_provider is not None:
            altitude = -1*self.navigation_provider.get_local_position_ned()[2]
        else:
            raise ValueError("No altitude information provider available.")

        inference = ImagingInference(bounding_box, altitude)
        return inference

    def _analyze_unit(self):
        self._analyze_image()

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

        if bounding_box:
            inference = self.get_inference(bounding_box)
            if inference:
                x, y = get_object_location(self.camera_attributes,
                                                inference)
                analysis_result = AnalysisResult(front=y, right=x)
                self.subscriberService(analysis_result)

class BeaconAnalysisDelegate(AnalysisDelegate):

    def __init__(self, beaconCoordinate: Tuple[float, float]) -> None:
        """
        Parameters:
            beaconCoordinate: Coordinates of the beacon you wish to assign. format: (latitude, longitude)
        """
        super().__init__()
        self.beaconCoordinate = beaconCoordinate

    def _analyze_unit(self):
        for subscriber in self.subscribers:
        #TODO: Implement logic to calculate offset between drones current position and beacon coordinates
            pass

    def set_beacon_coordinate(self, beaconCoordinate: Tuple[float, float]) -> None:
        self.beaconCoordinate = beaconCoordinate
