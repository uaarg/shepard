import math

import dronekit
from pymavlink import mavutil

class PrecisionLanding:

    """
    A Class to Handle the Precision Landing Messages of the drone"""

    def __init__(self, vehicle, landing_pad):
        self.vehicle = vehicle
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
    
    def send(self, im, bounding_box, fov=(62.2, 48.8)):
        """
        Receives the callback from ImageAnalysisDelegate (see imaging/analysis.py) and is executed when more landing information is recieved.
        
        For all parameters see imaging/analysis.py


        
        """

        #altitude = self.vehicle.location.global_relative_frame.alt

        altitude = 2

        horizontal_fov = fov[0]*math.pi/180
        vertical_fov = fov[1]*math.pi/180

        im_centre_x = im.width/2
        im_centre_y = im.height/2  

        land_x = self.landing_pad[0]
        land_y = self.landing_pad[1]

        size_x = bounding_box.size[0]
        size_y = bounding_box.size[1]
        
        position_x = bounding_box.position[0]
        position_y = bounding_box.position[1]

        centre_landing_x = position_x + (size_x/2)
        centre_landing_y = position_y + (size_y/2)

        angle_to_centre = (math.atan(centre_landing_y/centre_landing_x))

        angle_x = angle_to_centre*horizontal_fov
        angle_y = angle_to_centre*vertical_fov

        distance = math.cos((angle_to_centre))*altitude

        size_x = math.atan(((land_x/2)/altitude))*2
        size_y = math.atan(((land_y/2)/altitude))*2

        #self.__send_land_message(angle_x, angle_y, distance, size_x, size_y)

        print(f"Angle_x = {angle_x}\nAngle_y = {angle_y}\nDistance = {distance}\nsize_x = {size_x}\nsize_y = {size_y}")
        
