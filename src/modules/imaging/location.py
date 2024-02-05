from dataclasses import dataclass
import math
from src.modules.imaging.mavlink import MAVLinkDelegate


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

        if any(k in kwargs for k in ['pitch', 'roll', 'yaw']):
            pitch = kwargs.get('pitch', self._current_orientation.pitch)
            roll = kwargs.get('roll', self._current_orientation.roll)
            yaw = kwargs.get('yaw', self._current_orientation.yaw)

            self._current_orientation = Rotation(pitch, roll, yaw)


class MAVLinkLocationProvider:
    """
    Will provide location information based on information received as MAVLink messages.
    """

    def __init__(self, mavlink_delegate: MAVLinkDelegate):
        self.mavlink_delegate = mavlink_delegate
        self._location = None
        self._heading = None
        self._altitude = None
        self._orientation = None

        # Subscribe to the delegate's messages
        self.mavlink_delegate.subscribe(self._process_message)

    def _process_message(self, message):
        # This callback processes incoming MAVLink messages and updates the internal state
        if message.get_type() == 'GLOBAL_POSITION_INT':
            self._location = LatLng(message.lat / 1e7, message.lon / 1e7)
            self._altitude = message.alt / 1000.0  # Altitude in meters
            self._heading = Heading(message.hdg / 1e7)  # Heading in degrees
        elif message.get_type() == 'ATTITUDE':
            self._orientation = Rotation(pitch=math.degrees(message.pitch),
                                         roll=math.degrees(message.roll),
                                         yaw=math.degrees(message.yaw))

    def location(self) -> LatLng:
        if self._location is not None:
            return self._location
        else:
            raise ValueError("No valid location data available")

    def heading(self) -> Heading:
        if self._heading is not None:
            return self._heading
        else:
            raise ValueError("No valid heading data available")

    def altitude(self) -> float:
        if self._altitude is not None:
            return self._altitude
        else:
            raise ValueError("No valid altitude data available")

    def orientation(self) -> Rotation:
        if self._orientation is not None:
            return self._orientation
        else:
            raise ValueError("No valid orientation data available")
