import json
import threading

from src.modules.emu import Emu
from src.modules.slam.slam_provider import SLAMProvider


class SLAMEmuStreamer:
    """
    Continuously calls slam_provider.get_frame() and pushes each frame
    to Emu over WebSocket as a JSON "slam" message.
    Starts/stops on demand so bandwidth is only used while the SLAM tab is open.
    """

    def __init__(self, emu: Emu, slam_provider: SLAMProvider):
        self.emu = emu
        self.slam_provider = slam_provider
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
            self._thread = None

    def _stream_loop(self):
        while self._running:
            frame = self.slam_provider.get_frame()
            msg = json.dumps({
                "type": "slam_data",
                "point_cloud": frame.points.tolist(),
                "pose": {
                    "x": frame.pose.x,
                    "y": frame.pose.y,
                    "z": frame.pose.z,
                    "roll": frame.pose.roll,
                    "pitch": frame.pose.pitch,
                    "yaw": frame.pose.yaw,
                },
            })
            self.emu.send_msg(msg)
