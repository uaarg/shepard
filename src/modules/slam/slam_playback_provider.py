import time
from pathlib import Path

import numpy as np

from src.modules.slam.slam_provider import SLAMFrame, SLAMPose, SLAMProvider


class SLAMPlaybackProvider(SLAMProvider):
    """
    Replays a recorded SLAM session through the same SLAMProvider interface.
    Maintains original timing between frames so replay feels real-time.

    Pass loop=True to repeat the recording indefinitely.

    Usage:
        playback = SLAMPlaybackProvider("recordings/flight_01")
        streamer = SLAMEmuStreamer(emu, playback)
        streamer.start()
    """

    def __init__(self, recording_path: str, loop: bool = False):
        self._path = Path(recording_path)
        self._loop = loop
        self._frame_idx = 0
        self._frame_files = sorted((self._path / "frames").glob("*.npz"))
        self._prev_real_time: float | None = None
        self._prev_frame_time: float | None = None

        if not self._frame_files:
            raise FileNotFoundError(f"No frames found in {self._path / 'frames'}")

    @property
    def frame_count(self) -> int:
        return len(self._frame_files)

    def reset(self):
        self._frame_idx = 0
        self._prev_real_time = None
        self._prev_frame_time = None

    def get_frame(self) -> SLAMFrame:
        if self._frame_idx >= len(self._frame_files):
            if self._loop:
                self.reset()
            else:
                raise StopIteration("Recording playback complete")

        data = np.load(self._frame_files[self._frame_idx])
        timestamp = float(data["timestamp"][0])
        points = data["points"]
        pose_arr = data["pose"]

        pose = SLAMPose(
            x=float(pose_arr[0]),
            y=float(pose_arr[1]),
            z=float(pose_arr[2]),
            roll=float(pose_arr[3]),
            pitch=float(pose_arr[4]),
            yaw=float(pose_arr[5]),
        )

        # Reproduce original inter-frame timing
        if self._prev_frame_time is not None and self._prev_real_time is not None:
            frame_dt = timestamp - self._prev_frame_time
            elapsed = time.time() - self._prev_real_time
            sleep_time = frame_dt - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        self._prev_frame_time = timestamp
        self._prev_real_time = time.time()
        self._frame_idx += 1

        return SLAMFrame(points=points, pose=pose, timestamp=timestamp)
