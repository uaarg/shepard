from typing import Tuple

import pathlib
from PIL import Image
import numpy as np
import cv2


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

    def caputure_to(self, path: str | pathlib.Path):
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

    def __init__(self, dummy_image_path: str | pathlib.Path):
        self.og_im = Image.open(dummy_image_path)
        self.im = self.og_im  # Keep a copy of the original image for resizing.
        self.size = (self.im.width, self.im.height)

    def set_size(self, size: Tuple[int, int]):
        # Always resize from the original "dummy" image
        self.im = self.og_im.resize(size)
        self.size = size

    def capture(self) -> Image.Image:
        return self.im

class DebugCameraFromDir(CameraProvider):
    """
    Debug camera that returns an image from directory 'image_dir'
    containing only images
    """
    def __init__(self, image_dir: str | pathlib.Path):
        import os # used to get images in folder
        self.image_dir = image_dir
        self.imgs = os.listdir(image_dir)
        self.imgs = [ os.path.join(image_dir, file) for file in self.imgs ]
        if len(self.imgs) == 0:
            raise ValueError('no files in directory')
        self.index = 0
        
        # set size at first based on first image
        im = Image.open(self.imgs[self.index])
        self.size = (im.width, im.height)
    
    def set_size(self, size: Tuple[int, int]):
        # set size as each image is resized on load
        self.size = size 

    def capture(self) -> Image.Image:
        # return the next image in the directory
        filename = self.imgs[self.index]
        print(filename)
        self.index = (self.index + 1) % len(self.imgs)

        return Image.open(filename).resize(self.size)
 



class WebcamCamera(CameraProvider):
    """
    Debug camera source which uses the computer's webcam as the image source.
    """

    def __init__(self):
        self.cap = cv2.VideoCapture(0)  # 0 is typically the default webcam
        self.size = (640, 480)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.size[1])

    def set_size(self, size: Tuple[int, int]):
        self.size = size
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])

    def capture(self) -> Image.Image:
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame).resize(self.size)
        else:
            raise RuntimeError("Failed to capture image from webcam")


class RPiCamera(CameraProvider):
    """
    Note: Need picamera2 installed on the raspberry pi for this to work.
    Production camera source which uses the raspberry pi camera as the image
    source.
    """

    def __init__(self, cam_num: int):
        from picamera2 import Picamera2
        self.camera = Picamera2(cam_num)
        self.size = (640, 480)
        self.configure_camera()
        self.camera.start()
        print(self.camera.capture_metadata()['ScalerCrop'])
        print(self.camera.camera_controls['ScalerCrop'])

    def configure_camera(self):
        # Configuring camera properties
        config = self.camera.create_preview_configuration(
            main={"size": self.size})
        self.camera.configure(config)

    def set_size(self, size: Tuple[int, int]):
        self.size = size
        self.configure_camera()

    def capture(self) -> Image.Image:
        # Capture an image
        self.camera.start()
        capture_result = self.camera.capture_array()
        image = Image.fromarray(capture_result)
        return image
