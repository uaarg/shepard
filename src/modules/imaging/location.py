from dataclasses import dataclass


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

    # TODO: Implment the methods
    # TODO: Create tests (see test/test_location.py)

    def location(self) -> LatLng:
        raise NotImplementedError()

    def heading(self) -> Heading:
        raise NotImplementedError()

    def altitude(self) -> float:
        raise NotImplementedError()

    def orientation(self) -> Rotation:
        raise NotImplementedError()

    # TODO: implement this as well, need a type for new_location
    def debug_change_location(self, new_location):
        """
        Change the location reported by this DebugLocationProvider.
        """
        raise NotImplementedError()


class MAVLinkLocationProvider:
    """
    Will provide location information based on information received as mavlink
    messages.
    """

    # TODO: This one will be a little complex. Try working on it after
    # DebugLocationProvider is complete.

    def location(self) -> LatLng:
        raise NotImplementedError()

    def heading(self) -> Heading:
        raise NotImplementedError()

    def altitude(self) -> float:
        raise NotImplementedError()

    def orientation(self) -> Rotation:
        raise NotImplementedError()

