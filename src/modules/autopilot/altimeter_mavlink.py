import threading
import time
from typing import Optional

from pymavlink import mavutil

from src.modules.autopilot.altimeter import Altimeter


class MavlinkAltimeterProvider:
    """
    A class to handle altitude measurements from any Altimeter sensor
    and send them to the Pixhawk via MAVLink.
    """

    def __init__(self, sensor: Altimeter, connection_string: str, update_rate_hz: float = 10.0):
        """
        Initialize the MavlinkAltimeterProvider.

        Args:
            sensor: Altimeter sensor instance
            connection_string: MAVLink connection string (e.g., 'udp:127.0.0.1:14550')
            update_rate_hz: Rate at which to send altitude updates (Hz)
        """
        self.sensor = sensor
        self.connection_string = connection_string
        self.update_interval = 1.0 / update_rate_hz
        self._latest_altitude_mm = None
        self._latest_altitude_timestamp = 0
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._mavlink_connection = None
        self._tstart = None

    def start(self):
        """Start the altimeter thread."""
        if self._running:
            return

        try:
            self._tstart = time.time()

            # Initialize MAVLink connection
            self._mavlink_connection = mavutil.mavlink_connection(self.connection_string)
            # Wait for a heartbeat to ensure connection is established
            self._mavlink_connection.wait_heartbeat()
            print(f"MAVLink connection established on {self.connection_string}")

            # Start the measurement thread
            self._running = True
            self._thread = threading.Thread(target=self._measurement_loop, daemon=True)
            self._thread.start()
            print("Altimeter measurement thread started")

        except Exception as e:
            print(f"Failed to start MavlinkAltimeterProvider: {e}")
            self._running = False
            if self._mavlink_connection:
                self._mavlink_connection.close()

    def stop(self):
        """Stop the altimeter thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._mavlink_connection:
            self._mavlink_connection.close()
        print("Altimeter measurement thread stopped")

    def get_latest_altitude(self) -> Optional[float]:
        """
        Get the latest altitude measurement in millimeters.

        Returns:
            The latest altitude in mm, or None if no valid measurement is available
        """
        with self._lock:
            return self._latest_altitude_mm

    def get_latest_altitude_meters(self) -> Optional[float]:
        """
        Get the latest altitude measurement in meters.

        Returns:
            The latest altitude in meters, or None if no valid measurement is available
        """
        with self._lock:
            if self._latest_altitude_mm is not None:
                return self._latest_altitude_mm / 1000.0
            return None

    def _measurement_loop(self):
        """Continuous measurement loop that runs in a separate thread."""
        while self._running:
            try:
                start_time = time.time()

                # Get measurement from sensor
                self.sensor.measure()

                # Get the distance
                distance_mm = self.sensor.get_distance_mm()

                if distance_mm is not None:
                    # Update the latest altitude
                    with self._lock:
                        self._latest_altitude_mm = distance_mm
                        self._latest_altitude_timestamp = time.time()

                    # Send to Pixhawk via MAVLink
                    self._send_distance_sensor_message(distance_mm)

                # Sleep to maintain the desired update rate
                elapsed = time.time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                time.sleep(sleep_time)

            except Exception as e:
                print(f"Error in measurement loop: {e}")
                time.sleep(0.5)

    def _send_distance_sensor_message(self, distance_mm: float):
        """
        Send a DISTANCE_SENSOR MAVLink message to the Pixhawk.

        Args:
            distance_mm: Distance measurement in millimeters
        """
        if not self._mavlink_connection:
            return

        try:
            # Convert to centimeters for MAVLink message
            distance_cm = int(distance_mm / 10.0)

            # Create and send the DISTANCE_SENSOR message
            # Documentation: https://mavlink.io/en/messages/common.html#DISTANCE_SENSOR
            self._mavlink_connection.mav.distance_sensor_send(
                int((time.time() - self._tstart) * 1000),  # time_boot_ms
                self.sensor.min_distance_cm,  # min_distance (cm)
                self.sensor.max_distance_cm,  # max_distance (cm)
                distance_cm,  # current_distance (cm)
                self.sensor.mavlink_sensor_type,  # type (from sensor)
                self.sensor.sensor_id,  # id (unique ID for this sensor)
                mavutil.mavlink.MAV_SENSOR_ROTATION_PITCH_270,  # orientation (downward facing)
                0,  # covariance
            )

        except Exception as e:
            print(f"Error sending MAVLink message: {e}")
