import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np


@dataclass
class SLAMPose:
    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float


@dataclass
class SLAMFrame:
    points: np.ndarray  # shape (N, 3), metres, world frame
    pose: SLAMPose
    timestamp: float = field(default_factory=time.time)


class SLAMProvider(ABC):
    @abstractmethod
    def get_frame(self) -> SLAMFrame:
        raise NotImplementedError()
