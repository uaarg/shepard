import io
import threading
import time

from src.modules.emu import Emu
from src.modules.imaging.camera import SharedFrameCamera


class VideoEmuStreamer:
    """
    Continuously grabs frames from a SharedFrameCamera and pushes them
    to EMU's MJPEG /video endpoint at the given fps.
    """

    def __init__(self, emu: Emu, shared_cam: SharedFrameCamera, fps: int = 15, quality: int = 70):
        self.emu = emu
        self.shared_cam = shared_cam
        self.fps = fps
        self.quality = quality
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def _stream_loop(self):
        interval = 1 / self.fps
        while self._running:
            frame = self.shared_cam.capture()
            buf = io.BytesIO()
            frame.save(buf, format="JPEG", quality=self.quality)
            self.emu.send_video_frame(buf.getvalue())
            time.sleep(interval)
