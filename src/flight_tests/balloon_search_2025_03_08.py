import math
import os
import time

from mavctl import Navigator

from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider
from src.modules.autopilot.messenger import Messenger
from src.modules.imaging.detector import Detector

# Connection settings
CONN_STR = "udp:127.0.0.1:14550"
MESSENGER_PORT = 14550
MAVLINK_ALTITUDE_CONN_STR = CONN_STR

# Connect to the drone using mavctl
drone = Navigator(ip=CONN_STR)
messenger = Messenger(MESSENGER_PORT)

# Imaging setup
detector = Detector()

# Initialize the XM125 radar altimeter
radar_sensor = XM125(
    sensor_id=0,
    min_distance=250,
    max_distance=10000,
    average_window=5,
)

if not radar_sensor.begin():
    messenger.send("ERROR: Failed to initialize radar sensor")
    raise SystemExit(1)

# Create and start the MAVLink altimeter provider
mavlink_altimeter = MavlinkAltimeterProvider(radar_sensor, MAVLINK_ALTITUDE_CONN_STR)
mavlink_altimeter.start()

messenger.send("SHEPARD is online")

try:
    while not drone.wait_for_mode_and_arm():
        pass

    messenger.send("Executing mission")
    time.sleep(2)

    drone.takeoff(10)
    time.sleep(2)

    messenger.send("Starting balloon search")

    current_pic = 0

    dirs = os.listdir("tmp/log")
    ft_num = len(dirs)

    while True:
        step_size = 1  # meters
        last_pic = current_pic
        distance, direction, current_pic = detector.process_image_directory(
            directory_path=f"tmp/log/{ft_num}"
        )

        if current_pic == last_pic:
            continue

        if direction is not None:
            messenger.send(f"Balloon detected: Move {direction}, Distance: {distance:.2f}")

            if direction == "center":
                # Move in that direction, need to calculate the N and E offsets based on heading
                current_heading = drone.get_global_position().alt or 0.0  # placeholder, heading not available here
                metres_north_relative = step_size * math.sin(math.radians(current_heading))
                metres_east_relative = step_size * math.cos(math.radians(current_heading))
                drone.set_position_relative(metres_north_relative, metres_east_relative)
            elif direction == "right":
                drone.set_heading_relative(10)
            elif direction == "left":
                drone.set_heading_relative(-10)

        else:
            messenger.send("No balloons detected")
            drone.set_heading_relative(10)

except KeyboardInterrupt:
    messenger.send("Script interrupted by user")
except Exception as e:  # pylint: disable=broad-exception-caught
    messenger.send(f"ERROR: {str(e)}")
finally:
    messenger.send("Ending mission")

    # Ensure drone RTLs
    drone.return_to_launch()

    # Clean up
    messenger.send("Stopping altitude provider")
    mavlink_altimeter.stop()

    messenger.send("Altimeter test completed")
