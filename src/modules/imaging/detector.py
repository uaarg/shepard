from dataclasses import dataclass
from functools import cached_property, lru_cache

from typing import Optional

from PIL import Image

import math


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


class Detector:
    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        raise NotImplementedError()
