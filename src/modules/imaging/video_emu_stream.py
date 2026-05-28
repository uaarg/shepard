import io
import threading
import time

from PIL import Image

from src.modules.emu import Emu
from src.modules.imaging.camera import CameraProvider


class SharedFrameCamera(CameraProvider):
    """
    Wraps a CameraProvider and shares the latest captured frame across
    multiple consumers (e.g. video streamer + analysis pipeline) without
    both threads calling camera.capture() simultaneously.
    """

    def __init__(self, camera: CameraProvider, fps: int = 15):
        self._camera = camera
        self._fps = fps
        self._latest: Image.Image | None = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()

    def get_latest(self) -> Image.Image | None:
        with self._lock:
            return self._latest

    def capture(self) -> Image.Image:
        while True:
            with self._lock:
                if self._latest is not None:
                    return self._latest
            time.sleep(0.01)

    def _capture_loop(self):
        interval = 1 / self._fps
        while self._running:
            frame = self._camera.capture()
            with self._lock:
                self._latest = frame
            time.sleep(interval)


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
            frame = self.shared_cam.get_latest()
            if frame is not None:
                buf = io.BytesIO()
                frame.save(buf, format="JPEG", quality=self.quality)
                self.emu.send_video_frame(buf.getvalue())
            time.sleep(interval)
