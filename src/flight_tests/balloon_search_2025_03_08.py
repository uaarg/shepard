import math
import os
import threading
import time

from dronekit import connect, VehicleMode

from src.modules.autopilot import navigator
from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider

from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.detector import BalloonDetector
from src.modules.imaging.analysis import ImageAnalysisDelegate
from src.modules.imaging.analysis import ImageAnalysisDebugger
from src.modules.imaging.location import DebugLocationProvider

# Connection settings
CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14550
MAVLINK_ALTITUDE_CONN_STR = "tcp:127.0.0.1:14550"

# Connect to the drone
drone = connect(CONN_STR, wait_ready=False)

# Imaging setup
detector = BalloonDetector()
location_debugger = DebugLocationProvider()
debugger = ImageAnalysisDebugger()
camera = RPiCamera()
analysis = ImageAnalysisDelegate(detector=detector, camera=camera , location_provider=location_debugger, debugger=debugger)

# Initialize navigator
nav = navigator.Navigator(drone, MESSENGER_PORT)
nav.send_status_message("Altimeter test initializing")

# Initialize the XM125 radar altimeter
radar_sensor = XM125(
    sensor_id=0,
    min_distance=250,
    max_distance=10000,
    average_window=5
)

if not radar_sensor.begin():
    nav.send_status_message("ERROR: Failed to initialize radar sensor")
    drone.close()
    exit(1)

# Create and start the MAVLink altimeter provider
mavlink_altimeter = MavlinkAltimeterProvider(radar_sensor, MAVLINK_ALTITUDE_CONN_STR)
mavlink_altimeter.start()

nav.send_status_message("SHEPARD is online")

try:
    while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
        pass

    nav.send_status_message("Executing mission")
    time.sleep(2)

    nav.takeoff(10)
    time.sleep(2)

    nav.send_status_message("Starting balloon search")

    analysis.start()

except KeyboardInterrupt:
    nav.send_status_message("Script interrupted by user")
except Exception as e:
    nav.send_status_message(f"ERROR: {str(e)}")
finally:
    nav.send_status_message("Ending mission")

    # Ensure drone RTLs
    nav.return_to_launch()

    # Clean up
    nav.send_status_message("Stopping altitude provider")
    mavlink_altimeter.stop()

    nav.send_status_message("Altimeter test completed")
    drone.close()
