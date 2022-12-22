"""
Multiprocessing Task for Autopilot Functions

This file contains the "Main Loop" which sets up all autopilot 
functions to be executed by our script
"""
from multiprocessing import Queue
from enum import Enum

DroneStates = Enum('State', ['STOPPED', 'TAKEOFF', 'TRAVELLING', 'SEARCHING', 'LANDING'])

class AutopilotVars:
    state = DroneStates.SEARCHING
    # Add any additional variables being tracked here

def autopilot_main(new_images_queue, images_to_analyze, image_analysis_results):
    """
    Multiprocessing function called in a separate process for autopilot
    
    This function is executed once and should never return

    This function handles saving GPS information for new images, forwarding
    images for analysis if we are in a "searching" state, and sending waypoints
    to the autopilot controller (PixHawk)
    """

    # One time required setup
    # TODO: Put mavlink setup here

    while True:

        # Check if there are new images to get GPS
        while ~(new_images_queue.empty()):
            new_img_dict = new_images_queue.get()

            # TODO: Add code here to save the GPS position of the image from Mavlink

            # If the drone is searching for a landing pad or landing, we should analyze these images
            if (AutopilotVars.state == DroneStates.SEARCHING 
                    or AutopilotVars.state == DroneStates.LANDING):
                images_to_analyze.put({'img_path' : new_img_dict['img_path'], 'img_num' : new_img_dict['img_num']})

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



