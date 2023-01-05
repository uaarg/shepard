"""
This file contains utils for general autopilot functions

Separating these functions to this file allows the main function file 
to be more high level while working with the autopilot
"""
import sys
from math import sqrt
from dronekit import LocationGlobalRelative, Vehicle, APIException, connect

from image_analysis.inference_georeference import LonLat_To_XY, XY_To_LonLat

def connection_sequence(connection_string):
    """
    Connects to the Pixhawk Autopilot board over a wired MAVLINK connection
    """
    if connection_string != '':
            try:
                vehicle = connect(connection_string, heartbeat_timeout=15)

            # Bad TTY connection
            except OSError as e:
                print(f"Autopilot Connection Error: {e.strerror}")
                sys.exit()

            # API Error
            except APIException:
                print(f"Autopilot Timeout Error: {e.strerror}")
                sys.exit()
    else:
        print('No connection was specified for PixHawk, ignoring connection...')
        vehicle = None

    return vehicle

def takeoff_sequence(vehicle : Vehicle, target_alt) -> bool:
    """
    Performs the takeoff checks, then starts takeoff
    
    Note: This will Arm the drone, set it to GUIDED mode, and perform a takeoff
    Note: This function returns as soon as the takeoff starts, not until 
    """
    print("AutoPilot Starting Takeoff Procedure")

    print("Waiting for Vehicle to be armable")
    vehicle.wait_for_armable()
    
    print("Setting mode to GUIDED and waiting until mode applies")
    vehicle.wait_for_mode('GUIDED')

    print("Arming Drone")
    vehicle.arm()

    print("Starting Takeoff")

    vehicle.simple_takeoff(target_alt)

def get_searchpoint_offset(points_checked) -> tuple(float, float):
    """
    This function calculates the next offset the drone will search

    The return values are the meters north and meters east from 
    the central point.
    """
    
    # I think someone already did this algorithm
    # it calculates the next square the drone will search, starting at the nearest squares
    # then moving to the 

def is_vehicle_at_location(vehicle : Vehicle, location : LocationGlobalRelative, radius=1) -> bool:
    """
    This function returns true if the drone is within the radius of the
    specified location

    The radius is given in meters
    """
    current_loc = vehicle.location.global_relative_frame

    current_easting, current_northing = LonLat_To_XY(lon=current_loc.lon, lat=current_loc.lat)
    target_easting, target_northing = LonLat_To_XY(lon=location.lon, lat=location.lat)

    dist = sqrt((current_easting-target_easting)**2
                + (current_northing-target_northing)**2
                + (current_loc.alt-location.alt)**2)
    
    if dist > radius:
        return False

    # the distance is less than the radius
    return True

def get_horizontal_dist_to_location(vehicle : Vehicle, location : LocationGlobalRelative) -> float:
    """
    This function returns horizontal distance between the drone and a given location
    """
    current_loc = vehicle.location.global_relative_frame

    current_easting, current_northing = LonLat_To_XY(lon=current_loc.lon, lat=current_loc.lat)
    target_easting, target_northing = LonLat_To_XY(lon=location.lon, lat=location.lat)

    dist = sqrt((current_easting-target_easting)**2
                + (current_northing-target_northing)**2)
    
    return dist