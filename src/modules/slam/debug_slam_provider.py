import time

import numpy as np

from src.modules.slam.slam_provider import SLAMFrame, SLAMPose, SLAMProvider


class DebugSLAMProvider(SLAMProvider):
    """Returns a fake growing point cloud for testing the stream without hardware."""

    def __init__(self):
        self._t = 0

    def get_frame(self) -> SLAMFrame:
        time.sleep(0.1)
        self._t += 1
        points = np.random.randn(50, 3) * 0.5 + np.array([self._t * 0.1, 0, 0])
        pose = SLAMPose(x=self._t * 0.1, y=0.0, z=1.5, roll=0.0, pitch=0.0, yaw=0.0)
        return SLAMFrame(points=points, pose=pose)
