"""
Multiprocessing Task for Autopilot Functions

This file contains the "Main Loop" which sets up all autopilot 
functions to be executed by our script
"""
from multiprocessing import Queue
from enum import Enum
import dronekit
import sys, os
import json
from math import ceil
import time

DroneStates = Enum('State', ['STOPPED', 'TAKEOFF', 'TRAVELLING', 'SEARCHING', 'LANDING'])

class AutopilotVars:
    state = DroneStates.SEARCHING
    # Add any additional variables being tracked here

def autopilot_main(new_images_queue : Queue, images_to_analyze : Queue, image_analysis_results : Queue, 
                   camera_command_queue : Queue, connection_string : str):
    """
    Multiprocessing function called in a separate process for autopilot
    
    This function is executed once and should never return

    This function handles saving GPS information for new images, forwarding
    images for analysis if we are in a "searching" state, and sending waypoints
    to the autopilot controller (PixHawk)
    """

    # One time required setup
    if connection_string != '':
        try:
            vehicle = dronekit.connect(connection_string, heartbeat_timeout=15, source_system=0)

        # Bad TTY connection
        except OSError as e:
            print(f"Autopilot Connection Error: {e.strerror}")
            sys.exit()

        # API Error
        except dronekit.APIException as e:
            print(f"Autopilot Timeout Error: {e}")
            sys.exit()
    else:
        print('No connection was specified for PixHawk, ignoring connection...')
        vehicle = None
        
    @vehicle.on_message('MAV_CMD_IMAGE_START_CAPTURE')
    def listener(self, name, message):
        camera_command_queue.put("START_CAPTURE")

    @vehicle.on_message('MAV_CMD_IMAGE_STOP_CAPTURE')
    def listener(self, name, message):
        camera_command_queue.put("STOP_CAPTURE")

    while True:

        # Check if there are new images to get GPS
        while ~(new_images_queue.empty()):
            img_data = new_images_queue.get()

            log_image_georeference_data(vehicle, img_data['img_path'], img_data['img_num'], img_data['time'])

            # If the drone is searching for a landing pad or landing, we should analyze these images
            if (AutopilotVars.state == DroneStates.SEARCHING 
                    or AutopilotVars.state == DroneStates.LANDING):
                images_to_analyze.put({'img_path' : img_data['img_path'], 'img_num' : img_data['img_num']})

        # Check if there are new results to analyze
        while ~(image_analysis_results.empty()):
            new_img_results = image_analysis_results.get()

            if (AutopilotVars.state == DroneStates.SEARCHING 
                    or AutopilotVars.state == DroneStates.LANDING):
                # handle each found object in the image
                for object in new_img_results.results:
                    if object['type'] == 'blue landing pad':
                        print('Landing Pad Found, Updating Waypoints...')

                        # TODO: Implement Communication of the new waypoint at object['lat'], object['lon']
                        AutopilotVars.state = DroneStates.LANDING

def transmit_status(vehicle, status : str):
    """
    Transmits the provided status string over the Mavlink Connection
    """
    msg = vehicle.message_factory.statustext_encode(True)
    vehicle.send_mavlink(msg)

def transmit_image(vehicle, image_path : str):
    """
    Transmits the provided status string over the Mavlink Connection
    """

    with open(image_path, 'rb') as f:
        blob_data = bytearray(f.read())

    ENCAPSULATED_DATA_LEN = 253
    for msg_index, data_start_index in enumerate(range(0, len(blob_data), ENCAPSULATED_DATA_LEN)):
        data_seg = blob_data[data_start_index:data_start_index+ENCAPSULATED_DATA_LEN]
        print(data_seg)
        vehicle.message_factory.encapsulated_data_send(msg_index, data_seg)
        time.sleep(0.2)
    
    vehicle.message_factory.data_transmission_handshake_send(0, len(blob_data), 0, 0, ceil(len(blob_data) / ENCAPSULATED_DATA_LEN), ENCAPSULATED_DATA_LEN, 0)

def log_image_georeference_data(vehicle, img_path, img_num, timestamp):
    """
    Polls the Pixhawk for the latest GPS information for any image just taken

    This function sends a command to the PixHawk and returns the latest GPS position
    This position is then written to a text file '{img_num}.json' saving all the GPS positions
    """

    if vehicle is None:
        # We are not connected to a vehicle, this function should do nothing
        return

    json_file_path = f"{os.path.dirname(img_path)}/{img_num}.json"

    log = {
        'time'          : timestamp,
        'fixtype'       : vehicle.gps_0.fix_type,
        'lat'           : vehicle.location.global_frame.lat,
        'lon'           : vehicle.location.global_frame.lon,
        'relative_alt'  : vehicle.location.global_relative_frame.alt,
        'alt'           : vehicle.location.global_frame.alt,
        'pitch'         : vehicle.attitude.pitch,
        'roll'          : vehicle.attitude.roll,
        'yaw'           : vehicle.attitude.yaw
    }

    with open(json_file_path, "w") as json_file:
        json.dump(log, json_file, indent=2)


