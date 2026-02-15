from typing import Tuple

import pathlib
from PIL import Image
import numpy as np
import cv2
import depthai as dai
from dataclasses import dataclass


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

    def capture_to(self, path: str | pathlib.Path):
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


@dataclass
class DepthCapture:
    rgb: np.ndarray
    point_cloud: np.ndarray
    width: int
    height: int

    def get_point(self, x: int, y: int) -> np.ndarray:
        """Get the 3D coordinates relative to the camera frame (in mm) of a pixel).

        (x, y) are in pixel coordinates in the self.rgb frame."""
        idx = y * self.width + x
        p = self.point_cloud[idx]

        # I am not sure if this is possible...
        assert not np.any(np.isnan(p)), "Invalid depth at this point"

        return p

    def distance_between_points(self, x1: int, y1: int, x2: int, y2: int):
        """Get the physical distance between points from pixels in the rgb
        frame (x1, y1) and (x2, y2).

        Resulting distance is in mm."""
        p1 = self.get_point(x1, y1)
        p2 = self.get_point(x2, y2)

        dist = np.linalg.norm(p1 - p2)

        return dist


class OakdCamera(CameraProvider):
    """
    Manages an OAK-D device with on-demand capturing of 3D pictures (see DepthCapture).
    """

    def __init__(self, fps: int = 30):
        self._init_pipeline(fps)

    def _init_pipeline(self, fps: int):
        """Initialize the Depth AI pipeline (will be run on the OAK-D)"""
        pipeline = dai.Pipeline()

        camRgb = pipeline.create(dai.node.ColorCamera)
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoRight = pipeline.create(dai.node.MonoCamera)
        depth = pipeline.create(dai.node.StereoDepth)
        pointcloud = pipeline.create(dai.node.PointCloud)
        sync = pipeline.create(dai.node.Sync)
        xOut = pipeline.create(dai.node.XLinkOut)

        camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camRgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)
        camRgb.setIspScale(1, 3)
        camRgb.setFps(fps)

        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoLeft.setCamera("left")
        monoLeft.setFps(fps)

        monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoRight.setCamera("right")
        monoRight.setFps(fps)

        depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        depth.setLeftRightCheck(True)
        depth.setSubpixel(True)
        depth.setDepthAlign(dai.CameraBoardSocket.CAM_A)

        monoLeft.out.link(depth.left)
        monoRight.out.link(depth.right)
        depth.depth.link(pointcloud.inputDepth)

        camRgb.isp.link(sync.inputs["rgb"])
        pointcloud.outputPointCloud.link(sync.inputs["pcl"])

        sync.out.link(xOut.input)
        xOut.setStreamName("out")

        self.pipeline = pipeline

    def capture_with_depth(self) -> DepthCapture:
        """Capture a current 3D frame on the OAK-D.

        NOTE: .start() must have been called first. If it has not, this will raise Exception."""
        if not self.device or self.device.isClosed():
            raise Exception("No oakD connection, perhaps you forgot to call the .start() function")
        if self.queue is None:
            raise Exception("Queue does not exist")
        msg = self.queue.get()
        rgbFrame = msg["rgb"]
        cv_frame = rgbFrame.getCvFrame()
        rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
        rgb = np.array(rgb_frame)
        pcl = msg["pcl"]

        point_cloud = pcl.getPoints().astype(np.float64)
        height, width, _ = rgb.shape

        capture = DepthCapture(rgb, point_cloud, width, height)
        return capture

    def capture(self) -> Image.Image:
        capture = self.capture_with_depth()
        img = Image.fromarray(capture.rgb, "RGB")
        return img

    def start(self):
        """Start the depth-perception process on the OAK-D"""
        print("Starting OAK-D Connection")
        self.device = dai.Device(self.pipeline)
        self.queue = self.device.getOutputQueue("out", maxSize=1, blocking=False)

    def stop(self):
        """Stop the depth-perception process"""
        self.device.close()
        self.queue = None


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
        import os  # used to get images in folder
        self.image_dir = image_dir
        self.imgs = os.listdir(image_dir)
        self.imgs = [os.path.join(image_dir, file) for file in self.imgs]
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


class GazeboCamera(CameraProvider):
    """
    Video sourced from the Gazebo Simulator over UDP
    """

    def __init__(self):
        self.port = 5600

        gst_pipeline = (
            "udpsrc address=127.0.0.1 port=5600 ! "
            "application/x-rtp, encoding-name=H264 ! "
            "rtph264depay ! "
            "avdec_h264 ! "
            "videoconvert ! "
            "appsink"
        )
        self.size = (640, 480)
        self.cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            print("Failed to open UDP Stream")
            exit()

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

    def show_images(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Frame not received")
                break

            cv2.imshow("Gazebo Video Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        self.cap.release()
        cv2.destroyAllWindows()


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

    def __init__(self, cam_num: int = 0):
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
