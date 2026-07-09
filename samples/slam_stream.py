"""
Test SLAM streaming without any hardware.
Run this, open Emu, go to SLAM tab — you'll see a fake growing point cloud.
"""
import time

from src.modules.emu import Emu
from src.modules.slam.debug_slam_provider import DebugSLAMProvider
from src.modules.slam.slam_emu_streamer import SLAMEmuStreamer


def main():
    emu = Emu("tmp")
    emu.start_comms()
    time.sleep(1)

    streamer = SLAMEmuStreamer(emu, DebugSLAMProvider())
    emu.register_slam_streamer(streamer)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        streamer.stop()


if __name__ == "__main__":
    main()
