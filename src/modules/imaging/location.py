from dataclasses import dataclass
from pymavlink import mavutil
import math

@dataclass
class LatLng:
    """
    Latitude and longitude in WGS84 coordinates.
    """

    lat: float
    lng: float


@dataclass
class Heading:
    """
    Heading, as defined in an aeronautical sense, with respect to
    north. Measured in degrees.
    """

    heading: float


@dataclass
class Rotation:
    """
    Orientation of the drone using euler angles in degrees.
    """

    pitch: float
    roll: float
    yaw: float


class LocationProvider:
    """
    Provides the drone's current location and orientation as read from
    telemetry or a debug-source.
    """

    def location(self) -> LatLng:
        """
        Get the latest lat/lng location of the drone.
        """
        raise NotImplementedError()

    def heading(self) -> Heading:
        """
        Get the latest heading of the drone (with respect to north.)
        """
        raise NotImplementedError()

    def altitude(self) -> float:
        """
        Get the latest altitude of the drone in meters.
        """
        raise NotImplementedError()

    def orientation(self) -> Rotation:
        """
        Get the latest 3D orientation of the drone in it's inertial frame.
        """
        raise NotImplementedError()


class DebugLocationProvider:
    """
    Will return a series of given locations and orientations.
    """

    def __init__(self) -> None:
        self._current_location = LatLng(0.0, 0.0)
        self._current_heading = Heading(0.0)
        self._current_altitude = 0.0
        self._current_orientation = Rotation(0.0, 0.0, 0.0)

    def location(self) -> LatLng:
        return self._current_location

    def heading(self) -> Heading:
        return self._current_heading

    def altitude(self) -> float:
        return self._current_altitude

    def orientation(self) -> Rotation:
        return self._current_orientation

    def set_location(self, new_location):
        self._current_location = new_location

    def set_heading(self, new_heading):
        self._current_heading = new_heading

    def set_altitude(self, new_altitude):
        self._current_altitude = new_altitude

    def set_orientation(self, new_orientation):
        self._current_orientation = new_orientation

    def debug_change_location(self, **kwargs):
        """
        Change the location reported by this DebugLocationProvider.

        Keyword Arguments:
        lat -- Latitude
        lng -- Longitude
        heading -- Heading direction
        altitude -- Altitude
        pitch -- Pitch angle
        roll -- Roll angle
        yaw -- Yaw angle
        """
        if 'lat' in kwargs and 'lng' in kwargs:
            self._current_location = LatLng(kwargs['lat'], kwargs['lng'])

        if 'heading' in kwargs:
            self._current_heading = Heading(kwargs['heading'])

        if 'altitude' in kwargs:
            self._current_altitude = kwargs['altitude']

        if all(k in kwargs for k in ['pitch', 'roll', 'yaw']):
            self._current_orientation = Rotation(kwargs['pitch'],
                                                 kwargs['roll'], kwargs['yaw'])


class MAVLinkLocationProvider:
    """
    Will provide location information based on information received as mavlink
    messages.
    """
    def __init__(self, connection_string):
        self.mavlink_connection = mavutil.mavlink_connection(connection_string)
        self.current_message = None

    def _update_data(self):
        # Wait for a new message and update the current message
        self.current_message = self.mavlink_connection.recv_match(blocking=True)

    def location(self) -> LatLng:
        self._update_data()
        if self.current_message is not None and self.current_message.get_type() == 'GLOBAL_POSITION_INT':
            # Convert lat and lon from 1E7 scaled integer to float
            lat = self.current_message.lat / 1e7
            lon = self.current_message.lon / 1e7
            return LatLng(lat, lon)
        else:
            raise ValueError("No valid position data available")

    def heading(self) -> Heading:
        self._update_data()
        if self.current_message is not None and self.current_message.get_type() == 'VFR_HUD':
            return Heading(self.current_message.heading)
        else:
            raise ValueError("No valid heading data available")

    def altitude(self) -> float:
        self._update_data()
        if self.current_message is not None and self.current_message.get_type() == 'GLOBAL_POSITION_INT':
            # Convert altitude from millimeters to meters
            return self.current_message.alt / 1000.0
        else:
            raise ValueError("No valid altitude data available")

    def orientation(self) -> Rotation:
        self._update_data()
        if self.current_message is not None and self.current_message.get_type() == 'ATTITUDE':
            pitch = math.degrees(self.current_message.pitch)
            roll = math.degrees(self.current_message.roll)
            yaw = math.degrees(self.current_message.yaw)
            return Rotation(pitch, roll, yaw)
        else:
            raise ValueError("No valid orientation data available")
