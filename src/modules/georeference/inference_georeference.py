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
from math import sin, cos, tan, atan, radians, sqrt
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


def get_camera_dir_vector(focal_length, camera_angle, altitude, fovh, fovv, x, y) -> np.array:
    """
    Calculates the unit vector from an angled camera to an object at x, y pixel coordinates
    x and y are the normalized pixel coordinates between 0 and 1
    both fovs' are in radians.
    """

    direction_vector = np.zeros(3)

    #calculating image height and width in meters
    height = 2*focal_length*tan(fovv/2)
    width = 2*focal_length*tan(fovh/2)

    #pixels to meters conversion
    y_m = y*height
    x_m = x*width

    if(y_m > height/2):
        y_m = height - y_m
        theta_y = camera_angle - atan((height/2-y_m)/focal_length)
    elif(y_m <= height/2):
        theta_y = atan((height/2-y_m)/focal_length) + camera_angle
    
    if(x_m > width/2):
        x_m = width - x_m
        theta_x = -1*(atan((width/2-x_m)/focal_length))
    elif(x_m <= width/2):
        theta_x = atan((width/2-x_m)/focal_length)
    
    y_comp = altitude*tan(theta_y)
    x_comp = (altitude/cos(camera_angle))*tan(theta_x)
    
    direction_vector[0] = x_comp
    direction_vector[1] = y_comp
    direction_vector[2] = altitude

    return direction_vector

#not needed?
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

#TODO get measurements to calculate offset due to shifted position of camera from the gps
def calculate_object_offsets(
    height,
    x: float,
    y: float,
    focal_length,
    camera_angle,
    fovh,
    fovv) -> np.array:
    """
    Calculates the Easting and Northing Offsets for a given point in an image
    camera_angle is the angle between height and focal length of the camera
    Height is the posistion of the camera above ground level
    fovh, fovv is the field of view of the camera
    x and y are the normalized pixel coordinates between 0 and 1
    """
    

    # Calculate the absolute unit vector
    #absolute_unit_vector = adjust_dir_vector_orientation(
    #   camera_unit_vector, pitch, roll, yaw)

    # Calculate the scaling factor from the height
    #old code
    #scale = -height / absolute_unit_vector[2]

    #if (scale < 0):
        # detection is above horizon, this is an error
    #    print("Object was detected above horizon, ignoring...")
    #    return np.array([None, None])

    # Finally calculate the overall offsets
    #offsets = scale * absolute_unit_vector[:2]

    #return dir_vector


def get_object_location(camera_attributes: dict, inference: dict) -> tuple:
    """
    This calculates the location of the inference provided
    and returns the longitude, latitude in degrees
    """
    
    H_FOV = radians(62.2)
    V_FOV = radians(48.8)

    dir_vector = get_camera_dir_vector(camera_attributes["focal length"], camera_attributes["angle"],
                                       inference['relative_alt'], inference['x'], inference['y'],
                                       H_FOV, V_FOV,)

    lon, lat = XY_To_LonLat(dir_vector[0], dir_vector[1])

    return lon, lat