"""
This file contains the functions for integration with the imaging tasks

This allows the main autopilot task file to handle more high level functions
"""
import os
import json


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
        'time': timestamp,
        'fixtype': vehicle.gps_0.fix_type,
        'lat': vehicle.location.global_frame.lat,
        'lon': vehicle.location.global_frame.lon,
        'relative_alt': vehicle.location.global_relative_frame.alt,
        'alt': vehicle.location.global_frame.alt,
        'pitch': vehicle.attitude.pitch,
        'roll': vehicle.attitude.roll,
        'yaw': vehicle.attitude.yaw
    }

    with open(json_file_path, "w") as json_file:
        json.dump(log, json_file, indent=2)
