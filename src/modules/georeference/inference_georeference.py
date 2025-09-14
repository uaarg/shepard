"""
Functions for getting the location of objects we find in our images

This is done by assuming that we are looking a flat field
We can find the angle from our camera lens based on the pixel location
We can find the angle of the camera based on the Autopilot Roll, Yaw and Pitch

Note for this analysis, we use UTM coordinates.
This maps traditional Latitude and Longitude into an X Y coordinate grid
where X, Y are in meters
"""
# TODO: Requires a circular-import... but we only need these for type annotations
from dataclasses import dataclass
import numpy as np
from math import cos, tan, atan, radians, degrees, sqrt
import pyproj
from pyproj import Geod
import time

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..imaging.analysis import CameraAttributes, Inference

@dataclass
class Coordinate:
    '''
    Data Class for storing global coordinates

    '''

    lat: float
    lon: float
    

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

def Geofence_to_XY(origin, geofence):
    # Returns a new geofence which consists of position vectors in meters
    # Guys the Earth is like mostly flat right??

    try: 
        R = 6378137 # Radius of the Earth in meters

        new_fence = []

        origin_lon = origin[0]
        origin_lat = origin[1]

        origin_lon_rad = radians(origin_lon)
        origin_lat_rad = radians(origin_lat)

        for point in geofence:
            
            point_lon_rad = radians(point[0])
            point_lat_rad = radians(point[1])
            
            delta_lat = point_lat_rad - origin_lat_rad
            delta_lon = point_lon_rad - origin_lon_rad

            x = delta_lat * R
            y = delta_lon * cos((origin_lat_rad + point_lat_rad) / 2) * R
            
            new_fence.append((x, y))

        return new_fence

    except TypeError:
        return None
'''
def meters_to_LonLat(origin, points):

    R = 635900

    new_points = []

    origin_lon = origin[0]
    origin_lat = origin[1]

    origin_lon_rad = radians(origin_lon)
    origin_lat_rad = radians(origin_lat)

    for point in points:
        
        point_x = point[0]
        point_y = point[1]
        
        delta_lat = point_x / R
        delta_lon = point_y / (cos(origin_lat_rad + delta_lat / 2) * R)

        delta_lat = degrees(delta_lat)
        delta_lon = degrees(delta_lon)

        new_points.append((delta_lat + origin_lat, delta_lon + origin_lon))


    return new_points
'''
def meters_to_LonLat(origin, points):
    g = Geod(ellps='clrk66')
    new_points = []
    for point in points:
        az = atan(point[1] / point[0])
        dist = sqrt((point[0] ** 2 + point[1] ** 2))

        point_lon, point_lat, backaz = g.fwd(origin[0], origin[1], az, dist)
        new_points.append((point_lat, point_lon))

    return new_points


def pixel_to_rel_position(camera_attributes: 'CameraAttributes',
                          inference: 'Inference', fovh, fovv) -> np.array:
    """
    Calculates the unit vector from an angled camera to an object at x, y pixel coordinates
    x and y are the normalized pixel coordinates between 0 and 1
    both fovs' are in radians.
    """

    direction_vector = np.zeros(2)

    #calculating image height and width in meters
    height = 2 * camera_attributes.focal_length * tan(fovv / 2)
    width = 2 * camera_attributes.focal_length * tan(fovh / 2)

    #pixels to meters conversion
    y_m = inference.y * height
    x_m = inference.x * width

    if (y_m > height / 2):
        y_m = height - y_m
        theta_y = camera_attributes.angle - atan(
            (height / 2 - y_m) / camera_attributes.focal_length)
    elif (y_m <= height / 2):
        theta_y = atan(
            (height / 2 - y_m) /
            camera_attributes.focal_length) + camera_attributes.angle

    if (x_m > width / 2):
        x_m = width - x_m
        theta_x = -1 * (atan(
            (width / 2 - x_m) / camera_attributes.focal_length))
    elif (x_m <= width / 2):
        theta_x = atan((width / 2 - x_m) / camera_attributes.focal_length)

    y_comp = inference.relative_alt * tan(theta_y)
    x_comp = (inference.relative_alt /
              cos(camera_attributes.angle)) * tan(theta_x)

    offset = calculate_object_offsets()

    # NOTE: This correction was made because of the camera being upside down
    # This corrects the issues regarding the autopilot navigating to the wrong direction

    direction_vector[1] = -1*(x_comp + offset[0])
    direction_vector[0] = y_comp + offset[1]

    return direction_vector


#TODO get measurements to calculate offset due to shifted position of camera from the gps
def calculate_object_offsets() -> np.array:
    return np.array([0, 0])


def get_object_location(camera_attributes: 'CameraAttributes',
                        inference: 'Inference') -> tuple:
    """
    This calculates the location of the inference provided
    and returns the longitude, latitude in degrees
    """

    H_FOV = radians(62.2)
    V_FOV = radians(48.8)

    dir_vector = pixel_to_rel_position(
        camera_attributes,
        inference,
        H_FOV,
        V_FOV,
    )
    print("dir_vector", dir_vector)

    #lon, lat = XY_To_LonLat(dir_vector[0], dir_vector[1])

    return (dir_vector[0], dir_vector[1])
