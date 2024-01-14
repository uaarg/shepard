from typing import Tuple

import os
from PIL import Image
import numpy as np


class CameraProvider:
    """
    Manage a camera source. This could be the raspberry pi camera, a web cam,
    or a series of images.
    """

    def set_size(self, size: Tuple[int, int]):
        """
        Set the pixel width and height of all images taken by this camera.
        """
        # Should be implemented by deriving classes.
        raise NotImplementedError()

    def capture(self) -> Image.Image:
        """
        Captures a single image from the camera. This image will be of the size
        set by `set_size`.
        """
        # Should be implemented by deriving classes.
        raise NotImplementedError()

    def caputure_to(self, path: str | os.PathLike):
        """
        Captures a single image and saves it to `path`.
        """
        self.capture().save(path)

    def caputure_as_ndarry(self) -> np.ndarray:
        """
        Captures a single image returns it's numpy.ndarray representation. Will
        have shape (height, width, colors).
        """
        return np.array(self.capture())


class DebugCamera(CameraProvider):
    """
    Debug camera source which always returns the same image loaded from
    `dummy_image_path`.
    """

    def __init__(self, dummy_image_path: str | os.PathLike):
        self.og_im = Image.open(dummy_image_path)
        self.im = self.og_im  # Keep a copy of the original image for resizing.
        self.size = (self.im.width, self.im.height)

    def set_size(self, size: Tuple[int, int]):
        # Always resize from the original "dummy" image
        self.im = self.og_im.resize(size)
        self.size = size

    def capture(self) -> Image.Image:
        return self.im


class WebcamCamera(CameraProvider):
    """
    Debug camera source which uses the computer's webcam as the image source.
    """

    def set_size(self, size: Tuple[int, int]):
        # TODO
        raise NotImplementedError()

    def capture(self) -> Image.Image:
        # TODO
        raise NotImplementedError()


class RPiCamera(CameraProvider):
    """
    Production camera source which uses the raspberry pi camera as the image
    source.
    """

    def set_size(self, size: Tuple[int, int]):
        # TODO
        raise NotImplementedError()

    def capture(self) -> Image.Image:
        # TODO
        raise NotImplementedError()
