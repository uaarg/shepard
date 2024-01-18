from typing import Optional

from deps.labeller.benchmarks.detector import LandingPadDetector, BoundingBox
from .camera import CameraProvider


class ImageAnalysisDelegate:
    """
    Responsible for capturing pictures regularly, detecting any landing pads in
    those pictures and then providing the most recent estimate of the landing
    pad location from the camera's perspective.

    TODO: geolocate the landing pad using the drone's location.
    """

    def __init__(self, camera_provider: CameraProvider, detector: LandingPadDetector):
        self.camera_provider = camera_provider
        self.detector = detector

    def locate_landing_pad(self) -> Optional[BoundingBox]:
        """
        Capture an image and then locate a landing pad, if any, from that
        image. Returns None if no landing pad was found.
        """
        image = self.camera_provider.capture()
        return self.detector.predict(image)
