"""
Functions for getting the location of objects we find in our images

This is done by assuming that we are looking a flat field
We can find the angle from our camera lens based on the pixel location
We can find the angle of the camera based on the Autopilot Roll, Yaw and Pitch

Note for this analysis, we use UTM coordinates.
This maps traditional Latitude and Longitude into an X Y coordinate grid
where X, Y are in meters
"""
import json
import numpy as np
from math import sin, cos, tan, atan, radians
import pyproj


def LonLat_To_XY(lon, lat, zone=12):
    """
    Returns the Easting and Northing of given Lon, Lat on the WGS84
    Projection Model

    Input is in degrees, return is in meters
    """
    P = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', preserve_units=True)

    return P(lon, lat)


def XY_To_LonLat(x, y, zone=12):
    """
    Returns the Lon, Lat of given Easting, Northing on the WGS84
    Projection Model

    Input is in meters, return is in degrees
    """
    P = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', preserve_units=True)

    return P(x, y, inverse=True)


def get_camera_dir_vector(fovh, fovv, x: float, y: float) -> np.array:
    """
    Calculates the unit vector from a top down camera to an object at x, y pixel coordinates

    both fovs' are in radians, x and y are normalized between 0 and 1
    """

    # angle between x and z axis
    theta_x = atan((x - 0.5) * tan(fovh / 2) / 0.5)

    # angle between y and z axis
    theta_y = atan((0.5 - y) * tan(fovv / 2) / 0.5)

    # Direction Vector
    dir_v = np.array([sin(theta_x), sin(theta_y), -1])

    # Normalized Direction Vector
    return dir_v / np.linalg.norm(dir_v)


def adjust_dir_vector_orientation(input_dir: np.array, pitch, roll,
                                  yaw) -> np.array:
    """
    Rotates the direction vector using the camera pitch, roll and yaw

    All inputs are in radians
    """
    # Construct the rotation matrices for pitch, roll, and yaw
    Rx = np.array([[1, 0, 0], [0, cos(pitch), -sin(pitch)],
                   [0, sin(pitch), cos(pitch)]])

    Ry = np.array([[cos(roll), 0, sin(roll)], [0, 1, 0],
                   [-sin(roll), 0, cos(roll)]])

    Rz = np.array([[cos(yaw), sin(yaw), 0], [-sin(yaw), cos(yaw), 0],
                   [0, 0, 1]])

    return Rz @ Ry @ Rx @ input_dir


def calculate_object_offsets(
    height,
    pitch,
    roll,
    yaw,
    x: float,
    y: float,
    fovh=radians(62.2),
    fovv=radians(48.8)) -> np.array:
    """
    Calculates the Easting and Northing Offsets for a given point in an image

    Height is the posistion of the camera above ground level
    pitch, roll, and yaw are the orientation of the camera in radians
    fovh, fovv is the field of view of the camera
    x and y are the normalized pixel coordinates between 0 and 1
    """

    # Calculate the unit vector relative to the camera
    camera_unit_vector = get_camera_dir_vector(fovh, fovv, x, y)

    # Calculate the absolute unit vector
    absolute_unit_vector = adjust_dir_vector_orientation(
        camera_unit_vector, pitch, roll, yaw)

    # Calculate the scaling factor from the height
    scale = -height / absolute_unit_vector[2]

    if (scale < 0):
        # detection is above horizon, this is an error
        print("Object was detected above horizon, ignoring...")
        return np.array([None, None])

    # Finally calculate the overall offsets
    offsets = scale * absolute_unit_vector[:2]

    return offsets


def get_object_location(path, inference) -> tuple:
    """
    This function parses the latest gps information from each image
    then calculates the location of the inference provided

    returns the longitude, latitude in degrees
    """
    try:
        with open(path) as data_file:
            data = json.load(data_file)
    except EnvironmentError:
        print(f"Image Analysis could not open file {path}, ignoring...")
        return None, None

    # Raspberry Pi 2 Camera
    H_FOV = radians(62.2)
    V_FOV = radians(48.8)

    x_offset, y_offset = calculate_object_offsets(data['relative_alt'],
                                                  data['pitch'], data['roll'],
                                                  data['yaw'], inference['x'],
                                                  inference['y'], H_FOV, V_FOV)

    print(f"Image Location Offsets: {x_offset}, {y_offset}")

    if (None in (x_offset, y_offset)):
        # This is a false detection, offsets arent real
        return None, None
    easting, northing = LonLat_To_XY(data['lon'], data['lat'])

    lon, lat = XY_To_LonLat(easting + x_offset, northing + y_offset)

    return lon, lat
