"""
Multiprocessing Task for Autopilot Functions

This file contains the "Main Loop" which sets up all autopilot 
functions to be executed by our script
"""
from multiprocessing import Queue
from enum import Enum
import dronekit

from autopilot.autopilot_utils import get_horizontal_dist_to_location, connection_sequence
from autopilot.autopilot_imaging_integration import log_image_georeference_data

DroneStates = Enum('State', ['STOPPED', 'TAKEOFF', 'TRAVELLING', 'SEARCHING', 'TRACKING_PAD', 'LANDING'])

class AutopilotVars:
    state = DroneStates.SEARCHING 
    search_pattern_counter = 0 # This variable holds the number of locations checked in our search pattern
    img_being_processed = None
    next_destination = None
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
    vehicle = connection_sequence(connection_string)

    while True:

        # Check if there are new images to get GPS
        while ~(new_images_queue.empty()):
            img_data = new_images_queue.get()

            log_image_georeference_data(vehicle, img_data['img_path'], img_data['img_num'], img_data['time'])

            # If the drone is searching for a landing pad or landing, we should analyze these images
            if (AutopilotVars.state == DroneStates.SEARCHING 
                    or AutopilotVars.state == DroneStates.TRACKING):
                images_to_analyze.put({'img_path' : img_data['img_path'], 'img_num' : img_data['img_num']})

        # Check if there are new results to analyze
        while ~(image_analysis_results.empty()):
            new_img_results = image_analysis_results.get()

            autopilot_handle_inference_results(vehicle, new_img_results)

        # TODO: Put checks here for tracking if the drone is finished its preplanned route
        # TODO: Put checks here for tracking if the drone needs to change its current path
        # TODO: Check here if the drone has reached its target for the landing pad checks
        # TODO: Put check here for autopilot to go to the next search location if in SEARCHING mode


def autopilot_handle_inference_results(vehicle, new_img_results : dict):
    """
    Takes the output from the imaging analysis and determines next steps
    for our drone to take
    """
    if new_img_results['img_num'] != AutopilotVars.img_being_processed:
        # This was not the image we were looking for
        print(f"Recieved results for wrong img! Expected img {AutopilotVars.img_being_processed}, got {new_img_results['img_num']}")
        return
    
    # We should now filter our results so that only objects that are blue landing pads are considered
    new_img_results['results'] = [obj for obj in new_img_results['results'] if obj['type'] == 'blue landing pad']

    if new_img_results['results'] == []:
        # There were no objects located by our search
        AutopilotVars.search_pattern_counter += 1
        AutopilotVars.img_being_processed = None
        if AutopilotVars.state == DroneStates.TRACKING:
            # We lost track of our landing pad, go back to a search pattern
            AutopilotVars.state = DroneStates.SEARCHING
        return
    
    # Our image results must have at least 1 orange landing pad
    # We need to get the result with the highest confidence
    best_landing_pad = max(new_img_results['results'], key=lambda obj:obj['confidence'])

    # Determine the altitude we should make our next waypoint
    target = dronekit.LocationGlobalRelative(lat=best_landing_pad['lat'], lon=best_landing_pad['lon'])
    distance = get_horizontal_dist_to_location(vehicle, target)

    # round the altitude to the nearest 5m for simplicity
    current_alt = 5 * round(vehicle.location.global_relative_frame.alt/5)
    if distance >= 1:
        # we should move closer to our target before reducing our altitude
        target.alt = current_alt
    elif distance < 1 and current_alt >= 10:
        # We are close enough to procede landing
        target.alt = current_alt - 5
    elif distance > 0.3 and current_alt < 10: # distance between above if statement and this one
        # We should just move closer to within ~0.3m
        target.alt = 5
    else:
        # Ignore setting the next location, we can just land now
        vehicle.mode = dronekit.VehicleMode("LAND")
        AutopilotVars.state = DroneStates.LANDING
        return

    # We now have a target we should head to and take another image
    AutopilotVars.img_being_processed = None
    AutopilotVars.state = DroneStates.TRACKING
    AutopilotVars.next_destination = target
    vehicle.simple_goto(target)
