import math
import time

from dronekit import LocationGlobal, LocationGlobalRelative, VehicleMode, connect

from src.modules.autopilot.simulator import Simulator


# sim = Simulator()
# print(f"{sim.conn_str = } || {sim.gcs_conn_str = }")

conn_str = ""

drone = connect(conn_str, wait_ready=True)

# print("Connect GCS now.")
# time.sleep(25)


# def arm():
#     print("Arming")
#     drone.mode = VehicleMode("STABILIZE")
#     while not drone.is_armable:
#         time.sleep(1)
#         print("Not armable.")
#
#     drone.mode = VehicleMode("GUIDED")
#     drone.armed = True
#
#     while not drone.armed:
#         print("Waiting for arming...")
#         time.sleep(1)


def takeoff(target_alt):
    print("Taking off")
    drone.simple_takeoff(target_alt)

    while drone.location.global_relative_frame.alt < target_alt - 1:
        time.sleep(1)


def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the
    specified `original_location`. The returned LocationGlobal has the same `alt` value
    as `original_location`.

    The function is useful when you want to move the vehicle around specifying locations relative to
    the current vehicle position.

    The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.

    For more information see:
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """
    earth_radius = 6378137.0  # Radius of "spherical" earth
    # Coordinate offsets in radians
    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

    # New position in decimal degrees
    newlat = original_location.lat + (dLat * 180 / math.pi)
    newlon = original_location.lon + (dLon * 180 / math.pi)
    if type(original_location) is LocationGlobal:
        targetlocation = LocationGlobal(newlat, newlon, original_location.alt)
    elif type(original_location) is LocationGlobalRelative:
        targetlocation = LocationGlobalRelative(newlat, newlon, original_location.alt)
    else:
        raise Exception("Invalid Location object passed")

    return targetlocation


def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the
    earth's poles. It comes from the ArduPilot test code:
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5


def goto(dNorth, dEast, gotoFunction=drone.simple_goto):
    currentLocation = drone.location.global_relative_frame
    targetLocation = get_location_metres(currentLocation, dNorth, dEast)
    targetDistance = get_distance_metres(currentLocation, targetLocation)
    gotoFunction(targetLocation)

    while drone.mode.name == "GUIDED":  # Stop action if we are no longer in guided mode.
        remainingDistance = get_distance_metres(drone.location.global_frame, targetLocation)
        print("Distance to target: ", remainingDistance)
        if remainingDistance <= targetDistance * 0.01:  # Just below target, in case of undershoot.
            print("Reached target")
            break
        time.sleep(2)


if __name__ == "__main__":
    # arm()
    while not (drone.armed and drone.mode == VehicleMode("GUIDED")):
        print("Not in GUIDED mode or not armed.")

    takeoff(20)
    drone.groundspeed = 5

    print("West 25 m")
    goto(0, 25)

    print("East 25 m")
    goto(0, -25)

    drone.mode = VehicleMode("LAND")

    drone.close()
