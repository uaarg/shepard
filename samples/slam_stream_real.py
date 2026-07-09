"""
Real SLAM stream using OAK-D depth camera + XM125 altimeter + MAVLink pose.
Run on the Pi/ODroid with hardware connected.
"""
import time

from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.emu import Emu
from src.modules.imaging.camera import OakdCamera
from src.modules.imaging.location import MAVLinkLocationProvider
from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.slam.oakd_altimeter_slam_provider import OakdAltimeterSLAMProvider
from src.modules.slam.slam_emu_streamer import SLAMEmuStreamer

MAVLINK_CONNECTION = "udp:127.0.0.1:14550"


def main():
    # MAVLink for drone pose
    mavlink = MAVLinkDelegate(MAVLINK_CONNECTION)
    location_provider = MAVLinkLocationProvider(mavlink)

    # XM125 radar altimeter (I2C bus 1, default address 0x52)
    altimeter = XM125()
    if not altimeter.begin():
        print("XM125 init failed — check wiring")
        return

    # OAK-D depth camera
    oakd = OakdCamera(fps=10)
    oakd.start()

    # SLAM provider fuses the two
    slam_provider = OakdAltimeterSLAMProvider(oakd, altimeter, location_provider)

    # Emu server + streamer
    emu = Emu("tmp")
    emu.start_comms()
    time.sleep(1)

    streamer = SLAMEmuStreamer(emu, slam_provider)
    emu.register_slam_streamer(streamer)

    print("Ready — open Emu and go to the SLAM tab")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        streamer.stop()
        oakd.stop()


if __name__ == "__main__":
    main()
