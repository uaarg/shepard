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

DroneStates = Enum('State', ['STOPPED', 'TAKEOFF', 'TRAVELLING', 'SEARCHING', 'LANDING'])

class AutopilotVars:
    state = DroneStates.SEARCHING
    # Add any additional variables being tracked here

def autopilot_main(new_images_queue, images_to_analyze, image_analysis_results, connection_string):
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
            vehicle = dronekit.connect(connection_string, heartbeat_timeout=15)

        # Bad TTY connection
        except OSError as e:
            print(f"Autopilot Connection Error: {e.strerror}")
            sys.exit()

        # API Error
        except dronekit.APIException:
            print(f"Autopilot Timeout Error: {e.strerror}")
            sys.exit()
    else:
        print('No connection was specified for PixHawk, ignoring connection...')
        vehicle = None

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


