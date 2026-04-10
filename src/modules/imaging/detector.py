from functools import lru_cache
from typing import Optional

from PIL import Image
import numpy as np
import cv2


@dataclass
class Vec2:
    """2-component vector with float elements."""
    x: float
    y: float

    def __add__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vec2') -> 'Vec2':
        return Vec2(self.x - other.x, self.y - other.y)

    def __rmul__(self, scalar: float) -> 'Vec2':
        return Vec2(self.x * scalar, self.y * scalar)

    def __rtruediv__(self, scalar: float) -> 'Vec2':
        return Vec2(self.x / scalar, self.y / scalar)

    @cached_property
    def norm(self) -> float:
        """Return the euclidean norm of the vector"""
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self) -> 'Vec2':
        """Reduce the norm to 1 while preserving direction."""
        magnitude = self.norm
        if magnitude != 0:
            return Vec2(self.x / magnitude, self.y / magnitude)
        else:
            return Vec2(0, 0)

    @staticmethod
    def dot(v1: 'Vec2', v2: 'Vec2') -> float:
        """Compute the standard inner product between v1 and v2."""
        return v1.x * v2.x + v1.y * v2.y

    @staticmethod
    def min(v1: 'Vec2', v2: 'Vec2') -> 'Vec2':
        """Compute component-wise min of v1 and v2"""
        return Vec2(min(v1.x, v2.x), min(v1.y, v2.y))

    @staticmethod
    def max(v1: 'Vec2', v2: 'Vec2') -> 'Vec2':
        """Compute component-wise max of v1 and v2"""
        return Vec2(max(v1.x, v2.x), max(v1.y, v2.y))


class BoundingBox:

def __init__(self, position: Vec2, size: Vec2):
    self.position = position
    self.size = size

@lru_cache(maxsize=2)
def intersection(self, other: 'BoundingBox') -> float:
    top_left = Vec2.max(self.position, other.position)
    bottom_right = Vec2.min(self.position + self.size,
                            other.position + other.size)

    size = bottom_right - top_left

    intersection = size.x * size.y
    return max(intersection, 0)

def union(self, other: 'BoundingBox') -> float:
    intersection = self.intersection(other)
    if intersection == 0:
        return 0

    union = self.size.x * self.size.y + other.size.x * other.size.y - intersection
    return union

def intersection_over_union(self, pred: 'BoundingBox') -> Optional[float]:
    intersection = self.intersection(pred)
    if intersection == 0:
        return 0
    iou = intersection / self.union(pred)
    return iou


class BaseDetector:
    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        raise NotImplementedError()


class IrDetector(BaseDetector):

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        img = np.array(image)

        gray_img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        max_val = np.max(gray_img)  # returns maximum value of brightness
        if max_val < 200:
            return None  # lower threshold for intensity
        _, thresh = cv2.threshold(gray_img, max_val - 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # cv2.drawContours(thresh, contours, -1, (0, 255, 0), 2)

        if len(contours) == 0:
            return None

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

        return BoundingBox(Vec2(x, y), Vec2(w, h))


class ArucoDetector(LandingPadDetector):

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        img = np.array(image)
        if img.ndim == 2:
            gray = img
        elif img.shape[2] == 4:
            gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        else:
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

        # Add a white quiet-zone border so markers touching frame edges are still decodable.
        border = max(10, int(0.1 * min(gray.shape[:2])))
        padded = cv2.copyMakeBorder(
            gray,
            border,
            border,
            border,
            border,
            cv2.BORDER_CONSTANT,
            value=255,
        )

        # Support both older and newer OpenCV ArUco APIs.
        if hasattr(cv2.aruco, "getPredefinedDictionary"):
            aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_ARUCO_ORIGINAL)
        else:
            aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_ARUCO_ORIGINAL)

        if hasattr(cv2.aruco, "DetectorParameters"):
            params = cv2.aruco.DetectorParameters()
        else:
            params = cv2.aruco.DetectorParameters_create()

        if hasattr(cv2.aruco, "detectMarkers"):
            corners, ids, _ = cv2.aruco.detectMarkers(padded, aruco_dict, parameters=params)
            if ids is None or len(ids) == 0:
                # Some feeds produce inverted contrast; try once with inverted luminance.
                corners, ids, _ = cv2.aruco.detectMarkers(255 - padded, aruco_dict, parameters=params)
        else:
            detector = cv2.aruco.ArucoDetector(aruco_dict, params)
            corners, ids, _ = detector.detectMarkers(padded)
            if ids is None or len(ids) == 0:
                corners, ids, _ = detector.detectMarkers(255 - padded)

        if ids is None or len(ids) == 0:
            return None

        # Use the first detected marker.
        pts = corners[0].reshape(-1, 2)
        pts = pts - np.array([border, border], dtype=pts.dtype)

        # Clamp back to original frame in case padding pushes bounds slightly negative.
        pts[:, 0] = np.clip(pts[:, 0], 0, gray.shape[1] - 1)
        pts[:, 1] = np.clip(pts[:, 1], 0, gray.shape[0] - 1)
        x_min = float(np.min(pts[:, 0]))
        x_max = float(np.max(pts[:, 0]))
        y_min = float(np.min(pts[:, 1]))
        y_max = float(np.max(pts[:, 1]))

        width = x_max - x_min
        height = y_max - y_min
        return BoundingBox(Vec2(x_min, y_min), Vec2(width, height))

