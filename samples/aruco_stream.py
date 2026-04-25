import time

from src.modules.emu import Emu
from src.modules.imaging.detector import ArucoDetector
from src.modules.imaging.camera import DebugCamera
from src.modules.imaging.location import DebugLocationProvider
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.aruco_stream import ArucoEmuStreamer
from src.modules.imaging.video_emu_stream import SharedFrameCamera, VideoEmuStreamer


def main():
    emu = Emu("tmp")
    emu.start_comms()
    time.sleep(1)

    # Base camera — swap DebugCamera for RPiCamera/OakdCamera on real hardware
    base_camera = DebugCamera("res/test-image.jpeg")

    # SharedFrameCamera captures at 15fps; both video stream and analysis read from it
    shared_cam = SharedFrameCamera(base_camera, fps=15)
    shared_cam.start()

    # Video stream → EMU /video endpoint (browser: <img src="http://HOST:8080/video">)
    video_streamer = VideoEmuStreamer(emu, shared_cam, fps=15, quality=70)
    video_streamer.start()

    # ArUco detection pipeline reads latest frame from shared camera
    detector = ArucoDetector()
    location_provider = DebugLocationProvider()

    analysis = ImageAnalysisDelegate(detector, shared_cam, location_provider)
    aruco_streamer = ArucoEmuStreamer(emu, "tmp")
    analysis.subscribe(aruco_streamer.on_detection)
    analysis.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        analysis.stop()
        video_streamer.stop()
        shared_cam.stop()


if __name__ == "__main__":
    main()
