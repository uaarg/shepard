import math
import time
from datetime import datetime

import dronekit
from pymavlink import mavutil

from src.modules.autopilot.messenger import Messenger
from src.modules import imaging

class Navigator:
    """
    A class to handle navigation.
    """

    vehicle: dronekit.Vehicle = None
    POSITION_TOLERANCE = 1

    def __init__(self, vehicle, messenger_port):
        self.vehicle = vehicle
        self.mavlink_messenger = Messenger(messenger_port)

 

    def send_message(self, msg):
        self.__message(msg)

    def send_status_message(self, message):
        self.__message(message)

    def __message(self, msg):
        """
        Prints a message to the console.
        :param msg: The message to print.
        :return: None
        """

        print(f"SHEPARD_NAV: {msg}")
        self.mavlink_messenger.send(msg)

    def takeoff(self, target_alt):
        """
        Takes off to a given altitude.

        :param target_alt: The target altitude in meters.
        :return: True if successful, False otherwise.
        """

        self.__message(f"Taking off to {target_alt} m")

        self.vehicle.simple_takeoff(target_alt)

        while self.vehicle.location.global_relative_frame.alt < target_alt - 1:
            time.sleep(1)

        return True

    def set_position(self, lat, lon):
        """
        Moves the vehicle to a given position.

        :param lat: The latitude of the target position.
        :param lon: The longitude of the target position.
        :return: None
        """

        self.__message(f"Moving to {lat}, {lon}")

        target_location = dronekit.LocationGlobalRelative(
            lat, lon, self.vehicle.location.global_relative_frame.alt)
        self.vehicle.simple_goto(target_location)

        while self.vehicle.mode.name == "GUIDED":
            remaining_distance = self.__get_distance_metres(
                self.vehicle.location.global_relative_frame, target_location)
            self.__message(f"Distance to target: {remaining_distance} m")
            if remaining_distance <= self.POSITION_TOLERANCE:
                self.__message("Reached target")
                break
            time.sleep(2)

    def set_position_relative(self, d_north, d_east):
        """
        Moves the vehicle to a given position relative to its current position.

        :param d_north: The distance to move north in meters.
        :param d_east: The distance to move east in meters.
        :return: None
        """

        self.__message(f"Moving {d_north} m north and {d_east} m east")

        current_location = self.vehicle.location.global_relative_frame
        target_location = self.__get_location_metres(current_location, d_north,
                                                     d_east)

        self.vehicle.simple_goto(target_location)

        while self.vehicle.mode.name == "GUIDED":
            remaining_distance = self.__get_distance_metres(
                self.vehicle.location.global_relative_frame, target_location)
            self.__message(f"Distance to target: {remaining_distance} m")
            if remaining_distance <= self.POSITION_TOLERANCE:
                self.__message("Reached target")
                break
            time.sleep(2)

    def get_local_position_ned(self):
        # Gets the current location of the drone in the local NED frame
        location = self.vehicle.location.local_frame
        return (location.north, location.east, location.down)

    def get_global_position(self):
        location = self.vehicle.location.global_frame
        return (location.lat, location.lon, location.alt)

    def set_heading(self, heading):
        """
        Sets the heading of the vehicle.

        :param heading: The heading in degrees.
        :return: None
        """

        self.__message(f"Changing heading to {heading} degrees")

        # self.vehicle.commands.condition_yaw(heading)
        self.__condition_yaw(heading)

    def set_heading_relative(self, heading):
        """
        Sets the heading of the vehicle relative to its current heading.

        :param heading: The heading in degrees.
        :return: None
        """

        self.__message(
            f"Changing heading to {heading} degrees relative to current heading"
        )

        # self.vehicle.commands.condition_yaw(heading, relative=True)
        self.__condition_yaw(heading, relative=True)

    def set_altitude(self, altitude):
        """
        Sets the altitude of the vehicle.

        :param altitude: The altitude in meters.
        :return: None
        """

        self.__message(f"Setting altitude to {altitude} m")

        target_altitude = dronekit.LocationGlobalRelative(
            self.vehicle.location.global_relative_frame.lat,
            self.vehicle.location.global_relative_frame.lon,
            altitude,
        )
        self.vehicle.simple_goto(target_altitude)

        while self.vehicle.mode.name == "GUIDED":
            remaining_distance = abs(
                self.vehicle.location.global_relative_frame.alt -
                target_altitude.alt)
            self.__message(f"Distance to target: {remaining_distance} m")
            if remaining_distance <= self.POSITION_TOLERANCE:
                self.__message("Reached target")
                break
            time.sleep(2)

    def set_altitude_relative(self, altitude):
        """
        Sets the altitude of the vehicle relative to its current altitude.

        :param altitude: The altitude relative to current altitude in meters, positive value to ascend and negative to descend.
        :return: None
        """

        self.__message(
            f"Setting altitude to {altitude} m relative to current altitude")

        target_altitude = dronekit.LocationGlobalRelative(
            self.vehicle.location.global_relative_frame.lat,
            self.vehicle.location.global_relative_frame.lon,
            self.vehicle.location.global_relative_frame.alt + altitude,
        )
        self.vehicle.simple_goto(target_altitude)

        while self.vehicle.mode.name == "GUIDED":
            remaining_distance = self.__get_distance_metres(
                self.vehicle.location.global_relative_frame, target_altitude)
            self.__message(f"Distance to target: {remaining_distance} m")
            if remaining_distance <= self.POSITION_TOLERANCE:
                self.__message("Reached target")
                break
            time.sleep(2)

    def set_altitude_position(self,
                              lat,
                              lon,
                              alt,
                              battery=None,
                              voltage_hard_cutoff=22.4,
                              hard_cutoff_enable=False):
        """
        Sets the altitude and the position in absolute terms

        :param lat: The latitude of the target position.
        :param lon: The longitude of the target position.
        :param alt: The target altitude in metres
        :param battery: MAVLinkBatteryStatusProvider object
        :return: None
        """
        self.__message(f"Moving to lat: {lat} lon: {lon} alt: {alt}")

        target_altitude_position = dronekit.LocationGlobalRelative(
            lat, lon, alt)

        if hard_cutoff_enable:
            if self.sufficient_battery(battery, voltage_hard_cutoff):
                self.__message("--------Hard Cutoff reached----------")
                self.__message("--------Returning to Launch----------")
                self.return_to_launch()
                return

        self.vehicle.simple_goto(target_altitude_position)

        while self.vehicle.mode.name == "GUIDED":
            remaining_distance = self.__get_distance_metres(
                self.vehicle.location.global_relative_frame,
                target_altitude_position)
            self.__message(f"Distance to target: {remaining_distance} m")
            if remaining_distance <= self.POSITION_TOLERANCE:
                self.__message("Reached target")
                break
            time.sleep(2)

    def set_altitude_position_relative(self, d_north, d_east, alt):
        """
        Sets the altitude and the position relative to current position

        :param d_north: The distance to be moved north.
        :param d_east: The distance to be moved east.
        :param alt: Altitude to be moved in metres.
        :return: None
        """

        self.__message(
            f"Moving {d_north} m north and {d_east} m east and {alt} m in altitude"
        )

        current_location = self.vehicle.location.global_relative_frame
        target_location = self.__get_location_metres(current_location, d_north,
                                                     d_east)
        target_location.alt += alt

        self.vehicle.simple_goto(target_location)

        while self.vehicle.mode.name == "GUIDED":
            remaining_distance = self.__get_distance_metres(
                self.vehicle.location.global_relative_frame, target_location)
            self.__message(f"Distance to target: {remaining_distance} m")
            if remaining_distance <= self.POSITION_TOLERANCE:
                self.__message("Reached target")
                break
            time.sleep(2)

    def land(self):
        """
        Lands the vehicle.

        :return: None
        """

        self.__message("Landing")
        self.vehicle.mode = dronekit.VehicleMode("LAND")


    def precision_landing(self, lat, long, alt):
        """

        Experimenting with precision landing and utilizing the PyMavlink precision landing function.

        Creates and sends a precision landing message to the mavlink

        Requires landing target data
        """
        
        abort_land_alt = 5

        msg = self.vehicle.message_factory.mav_cmd_nav_land(abort_land_alt, # minimum altitude if landing is aborted
                                                            2, # Enable precision landing mode
                                                            0, # blank
                                                            0, # Desired Yaw Angle
                                                            lat, # Latitude of target
                                                            long, # Longitude of the target
                                                            alt  # Altitude of the ground in the current reference frame
                                                            )
        self.vehicle.send_mavlink(msg)


    def return_to_launch(self):
        """
        Returns the vehicle to its launch position.

        :return: None
        """

        self.__message("Returning to launch")
        self.vehicle.mode = dronekit.VehicleMode("RTL")

            

    def set_speed(self, speed):
        """
        Set the vehicle speed.

        :param speed: The target speed in m/s.
        :return: None
        """

        self.__message(f"Setting speed to {speed} m/s")
        msg = self.vehicle.message_factory.command_long_encode(
            0,
            0,  # target system, target component
            mavutil.mavlink.MAV_CMD_DO_CHANGE_SPEED,  # command
            0,  # confirmation
            0,  # speed type, ignored in Copter
            speed,  # speed
            0,
            0,
            0,
            0,
            0,  # ignore other parameters
        )

        self.vehicle.send_mavlink(msg)
        self.vehicle.flush()

    def __get_location_metres(self, original_location, d_north, d_east):
        """
        Returns a `LocationGlobalRelative` object containing the latitude/longitude `d_north` and `d_east` metres from the
        specified `original_location`. The returned `LocationGlobalRelative` has the same `alt` value as `original_location`.

        :param original_location: The reference `LocationGlobal`.
        :param d_north: The distance to the north in meters.
        :param d_east: The distance to the east in meters.
        :return: A `LocationGlobalRelative` object.
        """

        earth_radius = 6378137.0  # Radius of "spherical" earth
        # Coordinate offsets in radians
        d_lat = d_north / earth_radius
        d_lon = d_east / (earth_radius *
                          math.cos(math.pi * original_location.lat / 180))

        # New position in decimal degrees
        new_lat = original_location.lat + (d_lat * 180 / math.pi)
        new_lon = original_location.lon + (d_lon * 180 / math.pi)
        if type(original_location) is dronekit.LocationGlobal:
            target_location = dronekit.LocationGlobal(new_lat, new_lon,
                                                      original_location.alt)
        elif type(original_location) is dronekit.LocationGlobalRelative:
            target_location = dronekit.LocationGlobalRelative(
                new_lat, new_lon, original_location.alt)
        else:
            raise Exception("Invalid Location object passed")

        return target_location

    def __get_distance_metres(self, location_1, location_2):
        """
        Returns the ground distance in metres between two `LocationGlobal` or `LocationGlobalRelative` objects.

        This method is an approximation, and will not be accurate over large distances and close to the earth's poles.

        :param location_1: The first `LocationGlobal` or `LocationGlobalRelative` object.
        :param location_2: The second `LocationGlobal` or `LocationGlobalRelative` object.
        :return: The ground distance in metres.
        """

        d_lat = location_2.lat - location_1.lat
        d_lon = location_2.lon - location_1.lon

        return math.sqrt((d_lat * d_lat) + (d_lon * d_lon)) * 1.113195e5

    def __condition_yaw(self, heading, relative=False):
        if relative:
            is_relative = 1  # yaw relative to direction of travel
        else:
            is_relative = 0  # yaw is an absolute angle
        # create the CONDITION_YAW command using command_long_encode()
        msg = self.vehicle.message_factory.command_long_encode(
            0,
            0,  # target system, target component
            mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
            0,  # confirmation
            heading,  # param 1, yaw in degrees
            0,  # param 2, yaw speed deg/s
            1,  # param 3, direction -1 ccw, 1 cw
            is_relative,  # param 4, relative offset 1, absolute angle 0
            0,
            0,
            0,
        )  # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(msg)


    def send_land_message(angle_x, angle_y, distance, size_x, size_y):

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
