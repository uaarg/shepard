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
from math import sin, cos, tan, radians
import pyproj

def LonLat_To_XY(lon, lat, zone=12):
    """
    Returns the Easting and Westing of given Lat, Lon on the WGS84
    Projection Model
    
    Input is in degrees, return is in meters
    """
    P = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', preserve_units=True)

    return P(lon,lat)    

def XY_To_LonLat(x, y, zone=12):
    """
    Returns the Lat, Lon of given Easting, Northing on the WGS84
    Projection Model
    
    Input is in meters, return is in degrees
    """
    P = pyproj.Proj(proj='utm', zone=zone, ellps='WGS84', preserve_units=True)

    return P(x,y,inverse=True)    

def get_inference_location(path, inference):
    """
    This function parses the latest gps information from each image
    then calculates the location of the inference provided

    returns the longitude, latitude in degrees
    """
    with open(path + ".json") as data_file:
        data = json.load(data_file)
        
        # Correct data to degrees, meters
        data['lat'] = data['lat'] * 10**-7
        data['lon'] = data['lon'] * 10**-7
        data['relative_alt'] = data['relative_alt'] * 10**-3
        data['alt'] = data['alt'] * 10**-3

    H_FOV = 62.2 # degrees
    V_FOV = 48.8 # degrees

    camera_x_angle = (inference['x'] - 0.5) * H_FOV + data['roll']
    camera_y_angle = -(inference['y'] - 0.5) * V_FOV + data['pitch']

    offset_x = data['relative_alt'] * tan(radians(camera_x_angle))
    offset_y = data['relative_alt'] * tan(radians(camera_y_angle))

    # Rotate by yaw
    rotated_offset_x = offset_x * cos(radians(data['yaw'])) - offset_y * sin(radians(data['yaw']))
    rotated_offset_y = offset_x * sin(radians(data['yaw'])) + offset_y * cos(radians(data['yaw']))

    print(f"Image Location Offsets: {rotated_offset_x}, {rotated_offset_y}")

    easting, northing = LonLat_To_XY(data['lon'], data['lat'])

    lon, lat = XY_To_LonLat(easting + rotated_offset_x, northing + rotated_offset_y)

    return lon, lat


