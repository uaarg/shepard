import math
import os
import threading
import time

from dronekit import connect, VehicleMode

from src.modules.autopilot import navigator
from src.modules.autopilot.altimeter_xm125 import XM125
from src.modules.autopilot.altimeter_mavlink import MavlinkAltimeterProvider

from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.detector import Detector

# Connection settings
CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14550
MAVLINK_ALTITUDE_CONN_STR = "tcp:127.0.0.1:14550"

# Connect to the drone
drone = connect(CONN_STR, wait_ready=False)

# Imaging setup
detector = Detector()

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

    current_pic = 0
    
    dirs = os.listdir("tmp/log")
    ft_num = len(dirs)

    prev_movement_dir = None
    prev_movement_amnt = 60
    turn_count = 0

    while turn_count < 6: # 60 degrees * 6 = 360 => we completed a full circle without finding balloons
        step_size = 1  # meters
        last_pic = current_pic
        distance, direction, current_pic = detector.process_image_directory(directory_path=f"tmp/log/{ft_num}")

        if current_pic == last_pic: continue
        
        

        if direction is not None: # we saw balloon
            prev_movement_dir = direction # keep track in case balloon goes out of frame after previously found
            prev_movement_amnt //= 2
            nav.send_status_message(f"Balloon detected: Move {direction}, Distance: {distance:.2f}")

            if direction == "center":
                # Move in that direction, need to calculate the N and E offsets based on heading
                current_heading = drone.heading
                metres_north_relative = step_size * math.sin(math.radians(current_heading))
                metres_east_relative = step_size * math.cos(math.radians(current_heading))
                nav.set_position_relative(metres_north_relative, metres_east_relative)

            # best thing we could do is calculate the angle required to centre it
            # could also keep halving the distance
            elif direction == "right":
                nav.set_heading_relative(prev_movement_amnt)
            elif direction == "left":
                nav.set_heading_relative(-prev_movement_amnt)

        else: # we did nto see the balloon
            if prev_movement_dir == None:
                turn_count += 1
                nav.send_status_message("No balloons detected")
                # fov is around 62 degrees so if we move 30 degrees either direction we get a (mostly) new image
                nav.set_heading_relative(60)
            else:
                # we previously saw a balloon which we do not anymore
                prev_movement_amnt //= 2
                if prev_movement_dir == "right":
                    nav.set_heading_relative(-prev_movement_amnt) # if previously moved right balloon would be to the left
                else:
                    nav.set_heading_relative(prev_movement_amnt)


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
