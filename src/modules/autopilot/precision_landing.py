import math

import dronekit
from pymavlink import mavutil

class PrecisionLanding:

    """
    A Class to Handle the Precision Landing Messages of the drone"""

    def __init__(self, vehicle, altitude, landing_pad):
        self.vehicle = vehicle
        self.altitude = altitude
        self.landing_pad = landing_pad

    def __send_land_message(self, angle_x, angle_y, distance, size_x, size_y):

        """Sends a precision landing message to MAVlink
        
        https://mavlink.io/en/messages/common.html#LANDING_TARGET

        https://mavlink.io/en/services/landing_target.html

        :param angle_x: The x angular offset of landing zone from the center of a downward facing camera                        [Units: radians]
        :param angle_y: the y angular offset of the landing zone from the center of a downward facing camera                    [Units: radians]
        :param distance: The distance between the drone and the landing zone (the OVERALL distance not the x or y distance)     [Units: meters]
        :param size_x: The size of the landing target with respect to the x axis.                                               [Units: radians]
        :param size_y: the size of the landing target with respect to the y axis                                                [Units: radians]"""


        
        msg = self.vehicle.message_factory.landing_target_encode(
        angle_x,
        angle_y,
        distance,
        size_x,
        size_y
        
        )
        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()
    
    def send(self, im, lon, lat):
        """
        Receives the callback from ImageAnalysisDelegate (see imaging/analysis.py) and is executed when more landing information is recieved.
        
        For all parameters see imaging/analysis.py
        
        """
        
        land_x = self.landing_pad[0]
        land_y = self.landing_pad[1]

        size_x = math.atan((land_x/self.altitude))
        size_y = math.atan((land_y/self.altitude))

        distance = math.cos((lon*180/math.pi))*self.altitude

        self.__send_land_message(lat, lon, distance, size_x, size_y)
