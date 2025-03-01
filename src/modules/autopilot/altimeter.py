from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class MovingAverage:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.values = []

    def add(self, value):
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)

    def get_average(self):
        if not self.values:
            return None
        return sum(self.values) / len(self.values)

    def is_valid(self):
        return len(self.values) == self.window_size

    def reset(self):
        """Clear all values"""
        self.values = []


class Altimeter(ABC):
    """
    Abstract base class for altimeter sensors.
    All altimeter implementations should inherit from this class.
    """

    # MAVLink sensor type constants
    SENSOR_TYPE_LASER = 0
    SENSOR_TYPE_ULTRASOUND = 1
    SENSOR_TYPE_INFRARED = 2
    SENSOR_TYPE_RADAR = 3
    SENSOR_TYPE_UNKNOWN = 4

    def __init__(self, sensor_id: int = 0, min_distance_mm: int = 0, max_distance_mm: int = 0):
        """
        Initialize the altimeter.

        Args:
            sensor_id: Unique ID for this sensor (used in MAVLink messages)
            min_distance_mm: Minimum measurable distance in millimeters
            max_distance_mm: Maximum measurable distance in millimeters
        """
        self.sensor_id = sensor_id
        self.min_distance_mm = min_distance_mm
        self.max_distance_mm = max_distance_mm
        self.state = 0  # Generic value, interpretation depends on sensor type

    @abstractmethod
    def begin(self) -> bool:
        """
        Initialize the sensor hardware.

        Returns:
            True if initialization was successful, False otherwise
        """
        pass

    @abstractmethod
    def measure(self) -> List[Dict[str, Any]]:
        """
        Perform a measurement.

        Returns:
            A list of measurement data (format depends on sensor type)
        """
        pass

    @abstractmethod
    def get_distance_mm(self) -> Optional[float]:
        """
        Get the latest distance measurement in millimeters.

        Returns:
            The distance in millimeters, or None if no valid measurement is available
        """
        pass

    def get_distance_m(self) -> Optional[float]:
        """
        Get the latest distance measurement in meters.

        Returns:
            The distance in meters, or None if no valid measurement is available
        """
        distance_mm = self.get_distance_mm()
        if distance_mm is not None:
            return distance_mm / 1000.0
        return None

    @property
    def min_distance_cm(self) -> int:
        """Get minimum distance in centimeters for MAVLink messages"""
        return int(self.min_distance_mm / 10)

    @property
    def max_distance_cm(self) -> int:
        """Get maximum distance in centimeters for MAVLink messages"""
        return int(self.max_distance_mm / 10)

    @property
    @abstractmethod
    def mavlink_sensor_type(self) -> int:
        """
        Get the MAVLink sensor type for this altimeter.

        Returns:
            An integer representing the MAVLink sensor type
        """
        pass
