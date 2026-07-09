import json
import time
from pathlib import Path

import numpy as np

from src.modules.slam.slam_provider import SLAMFrame, SLAMProvider


class SLAMRecorder(SLAMProvider):
    """
    Wraps any SLAMProvider and records every frame to disk while passing
    it through unchanged. Acts as a transparent decorator — plug it in
    between any provider and the streamer and recording happens automatically.

    Usage:
        recorder = SLAMRecorder(real_provider, "recordings/flight_01")
        recorder.start_recording()
        streamer = SLAMEmuStreamer(emu, recorder)   # recorder IS a SLAMProvider
        streamer.start()
        ...
        recorder.stop_recording()
    """

    def __init__(self, provider: SLAMProvider, recording_path: str):
        self._provider = provider
        self._path = Path(recording_path)
        self._frame_idx = 0
        self._start_time: float | None = None
        self._recording = False

    def start_recording(self):
        self._path.mkdir(parents=True, exist_ok=True)
        (self._path / "frames").mkdir(exist_ok=True)
        self._start_time = time.time()
        self._frame_idx = 0
        self._recording = True
        print(f"Recording started → {self._path}")

    def stop_recording(self):
        self._recording = False
        self._save_metadata()
        print(f"Recording saved ({self._frame_idx} frames) → {self._path}")

    def get_frame(self) -> SLAMFrame:
        frame = self._provider.get_frame()
        if self._recording:
            self._save_frame(frame)
        return frame

    def _save_frame(self, frame: SLAMFrame):
        frame_path = self._path / "frames" / f"{self._frame_idx:06d}.npz"
        np.savez_compressed(
            frame_path,
            timestamp=np.array([frame.timestamp]),
            points=frame.points,
            pose=np.array([
                frame.pose.x, frame.pose.y, frame.pose.z,
                frame.pose.roll, frame.pose.pitch, frame.pose.yaw,
            ]),
        )
        self._frame_idx += 1

    def _save_metadata(self):
        duration = (time.time() - self._start_time) if self._start_time else 0.0
        metadata = {
            "frame_count": self._frame_idx,
            "created_at": self._start_time,
            "duration_sec": duration,
        }
        with open(self._path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
