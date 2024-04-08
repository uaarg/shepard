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


def pixel_to_rel_position(focal_length, camera_angle, altitude, fovh, fovv, x, y) -> np.array:
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
    pass


def get_object_location(camera_attributes: dict, inference: dict) -> tuple:
    """
    This calculates the location of the inference provided
    and returns the longitude, latitude in degrees
    """
    
    H_FOV = radians(62.2)
    V_FOV = radians(48.8)

    dir_vector = pixel_to_rel_position(camera_attributes["focal length"], camera_attributes["angle"],
                                       inference['relative_alt'], inference['x'], inference['y'],
                                       H_FOV, V_FOV,)

    lon, lat = XY_To_LonLat(dir_vector[0], dir_vector[1])

    return (lon, lat)