import math
import time

import dronekit
from pymavlink import mavutil

from src.modules.autopilot.messenger import Messenger


class Navigator:
    """
    A class to handle navigation.
    """

    vehicle: dronekit.Vehicle = None
    POSITION_TOLERANCE = 1.0  # m

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
        self.mavlink_messenger.send(msg, "SHEPARD_NAV")

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
        target_distance = self.__get_distance_metres(current_location,
                                                     target_location)

        self.vehicle.simple_goto(target_location)

        while self.vehicle.mode.name == "GUIDED":
            remaining_distance = self.__get_distance_metres(
                self.vehicle.location.global_relative_frame, target_location)
            self.__message(f"Distance to target: {remaining_distance} m")
            if remaining_distance <= self.POSITION_TOLERANCE:
                self.__message("Reached target")
                break
            time.sleep(2)

    def set_heading(self, heading):
        """
        Sets the heading of the vehicle.

        :param heading: The heading in degrees.
        :return: None
        """

        self.__message(f"Setting heading to {heading} degrees")

        self.__condition_yaw(heading)

    def set_heading_relative(self, heading):
        """
        Sets the heading of the vehicle relative to its current heading.

        :param heading: The heading in degrees.
        :return: None
        """

        self.__message(f"Changing heading by {heading} degrees relative")

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
            self.vehicle.location.global_relative_frame.lon, altitude)
        self.vehicle.simple_goto(target_altitude)

    def set_altitude_relative(self, altitude):
        """
        Sets the altitude of the vehicle relative to its current altitude.

        :param altitude: The altitude relative to current altitude in meters, positive value to ascend and negative to descend.
        :return: None
        """

        self.__message(f"Changing altitude to {altitude} m relative")

        target_altitude = dronekit.LocationGlobalRelative(
            self.vehicle.location.global_relative_frame.lat,
            self.vehicle.location.global_relative_frame.lon,
            self.vehicle.location.global_relative_frame.alt + altitude)
        self.vehicle.simple_goto(target_altitude)

    def set_altitude_position(self, lat, lon, alt):
        """
        Sets the altitude and the position in absolute terms

        :param lat: The latitude of the target position.
        :param lon: The longitude of the target position.
        :param alt: The target altitude in metres
        :return: None
        """
        self.__message(f"Moving to lat: {lat} lon: {lon} alt: {alt}")

        target_altitude_position = dronekit.LocationGlobalRelative(
            lat, lon, alt)

        self.vehicle.simple_goto(target_altitude_position)

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
        target_distance = self.__get_distance_metres(current_location, target_location)

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

    def return_to_launch(self):
        """
        Returns the vehicle to its launch position.

        :return: None
        """

        self.__message("Returning to launch")
        self.vehicle.mode = dronekit.VehicleMode("RTL")

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
            0)  # param 5 ~ 7 not used
        # send command to vehicle
        self.vehicle.send_mavlink(msg)
