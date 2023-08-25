import time
from math import sqrt
from dronekit import LocationGlobalRelative, Vehicle, VehicleMode
from image_analysis.inference_georeference import LonLat_To_XY


def transmit_text(vehicle, text: str):
    """
    Transmits the provided status string over the Mavlink Connection
    """
    vehicle.message_factory.statustext_send(severity=5, text=text.encode())


def takeoff(vehicle, target_altitude=10):
    """Script to handle when RPi is set in Takeoff Mode"""

    if not vehicle.is_armable:
        transmit_text(vehicle, "Vehicle not Armable")
        return

    print("Starting Takeoff")

    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    # Wait until arming is confirmed
    while not vehicle.armed:
        print("Waiting to arm")
        time.sleep(1)

    vehicle.simple_takeoff(target_altitude)

    while True:
        if vehicle.location.global_relative_frame.alt >= target_altitude * 0.95:
            break

        time.sleep(1)

    transmit_text(vehicle, "Takeoff Completed")


def follow_mission(vehicle):
    """Script to handle when RPi is set in FOLLOW_MISSION Mode"""

    print("Setting Drone to Follow Waypoints")

    vehicle.mode = VehicleMode("AUTO")

    transmit_text(vehicle, "Following Planned Waypoints")


def initiate_landing_search(vehicle):
    """Script to handle when RPi is set in LANDING_SEARCH Mode"""

    print("Setting Drone to follow positions")

    vehicle.mode = VehicleMode("GUIDED")

    transmit_text(vehicle, "Following Imaging Guidance")


def land(vehicle):
    """Script to handle when RPi is set in LAND Mode"""

    print("Setting Drone to land in place")

    vehicle.mode = VehicleMode("LAND")

    transmit_text(vehicle, "Drone is landing")


def get_searchpoint_offset(points_checked) -> tuple([float, float]):
    """
    This function calculates the next offset the drone will search

    The return values are the meters north and meters east from
    the central point.
    """

    # I think someone already did this algorithm
    # it calculates the next square the drone will search, starting at the nearest squares
    # then moving to the


def is_vehicle_at_location(vehicle: Vehicle,
                           location: LocationGlobalRelative,
                           radius=1) -> bool:
    """
    This function returns true if the drone is within the radius of the
    specified location

    The radius is given in meters
    """
    current_loc = vehicle.location.global_relative_frame

    current_easting, current_northing = LonLat_To_XY(lon=current_loc.lon,
                                                     lat=current_loc.lat)
    target_easting, target_northing = LonLat_To_XY(lon=location.lon,
                                                   lat=location.lat)

    dist = sqrt((current_easting - target_easting)**2 +
                (current_northing - target_northing)**2 +
                (current_loc.alt - location.alt)**2)

    if dist > radius:
        return False

    # the distance is less than the radius
    return True


def get_horizontal_dist_to_location(vehicle: Vehicle,
                                    location: LocationGlobalRelative) -> float:
    """
    This function returns horizontal distance between the drone and a given location
    """
    current_loc = vehicle.location.global_relative_frame

    current_easting, current_northing = LonLat_To_XY(lon=current_loc.lon,
                                                     lat=current_loc.lat)
    target_easting, target_northing = LonLat_To_XY(lon=location.lon,
                                                   lat=location.lat)

    dist = sqrt((current_easting - target_easting)**2 +
                (current_northing - target_northing)**2)

    return dist
