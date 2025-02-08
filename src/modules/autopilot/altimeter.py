import smbus2
import time
from enum import Enum
from typing import Optional, List, Dict, Tuple


DEBUG = False

class SensorError(Exception):
    """Base exception class for sensor errors"""
    pass


class SensorState(Enum):
    """Enum to track sensor state"""
    UNINITIALIZED = 0
    INITIALIZED = 1
    ERROR = 2
    NEEDS_CALIBRATION = 3


class SensorReflectorShape(Enum):
    """Enum to define reflector shape"""
    GENERIC = 1
    PLANAR = 2


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


class XM125:
    # Register addresses
    REG_VERSION = 0x0000
    REG_PROTOCOL_STATUS = 0x0001
    REG_MEASURE_COUNTER = 0x0002
    REG_DETECTOR_STATUS = 0x0003
    REG_DISTANCE_RESULT = 0x0010
    REG_PEAK0_DISTANCE = 0x0011
    REG_PEAK0_STRENGTH = 0x001b
    REG_START = 0x0040
    REG_END = 0x0041
    REG_COMMAND = 0x0100
    REG_REFLECTOR_SHAPE = 0x004b

    # Command values
    CMD_APPLY_CONFIG_AND_CALIBRATE = 1
    CMD_MEASURE_DISTANCE = 2
    CMD_RECALIBRATE = 5
    CMD_RESET_MODULE = 1381192737

    # Config values
    REFLECTOR_SHAPE = SensorReflectorShape.PLANAR.value

    # Status masks
    DETECTOR_STATUS_BUSY_MASK = 0x80000000
    DISTANCE_RESULT_NUM_DISTANCES_MASK = 0x0000000f
    DISTANCE_RESULT_NEAR_START_EDGE = 0x00000100
    DISTANCE_RESULT_CALIBRATION_NEEDED = 0x00000200
    DISTANCE_RESULT_MEASURE_DISTANCE_ERROR = 0x00000400

    # Error recovery constants
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds
    ERROR_TIMEOUT = 5.0  # seconds

    def __init__(self, bus=1, address=0x52, average_window=5):
        self.bus = smbus2.SMBus(bus)
        self.address = address
        self.distance_avg = MovingAverage(average_window)
        self.strength_avg = MovingAverage(average_window)
        self.state = SensorState.UNINITIALIZED
        self.last_error_time = 0
        self.error_count = 0
        self.consecutive_errors = 0

    def _read_register(self, reg_addr) -> Optional[int]:
        """Read a 32-bit register value with error handling."""
        try:
            write = smbus2.i2c_msg.write(self.address, [(reg_addr >> 8) & 0xFF, reg_addr & 0xFF])
            read = smbus2.i2c_msg.read(self.address, 4)

            if DEBUG:
                print(f"\nREAD OPERATION:")
                print(f"  Register: 0x{reg_addr:04x}")
                print(f"  Sending address bytes: MSB=0x{(reg_addr >> 8) & 0xFF:02x}, LSB=0x{reg_addr & 0xFF:02x}")

            self.bus.i2c_rdwr(write, read)
            data = list(read)
            value = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

            if DEBUG:
                print(f"  Received bytes: [0x{data[0]:02x}, 0x{data[1]:02x}, 0x{data[2]:02x}, 0x{data[3]:02x}]")
                print(f"  Decoded value: 0x{value:08x} ({value})")

            return value
        except IOError as e:
            self._handle_error(f"I/O error reading register 0x{reg_addr:04x}: {e}")
            return None

    def _write_register(self, reg_addr: int, value: int) -> bool:
        """Write a 32-bit register value with error handling."""
        try:
            data = [
                (reg_addr >> 8) & 0xFF,  # Address to slave [15:8]
                reg_addr & 0xFF,  # Address to slave [7:0]
                (value >> 24) & 0xFF,  # Data to slave [31:24]
                (value >> 16) & 0xFF,  # Data to slave [23:16]
                (value >> 8) & 0xFF,  # Data to slave [15:8]
                value & 0xFF  # Data to slave [7:0]
            ]

            if DEBUG:
                print(f"\nWRITE OPERATION:")
                print(f"  Register: 0x{reg_addr:04x}")
                print(f"  Value to write: 0x{value:08x} ({value})")
                print(f"  Sending bytes: {[f'0x{b:02x}' for b in data]}")

            self.bus.write_i2c_block_data(self.address, data[0], data[1:])
            return True
        except IOError as e:
            self._handle_error(f"I/O error writing register 0x{reg_addr:04x}: {e}")
            return False

    def _handle_error(self, error_msg: str):
        """Handle errors and implement recovery logic."""
        current_time = time.time()
        self.consecutive_errors += 1
        self.error_count += 1

        print(f"Error: {error_msg}")
        print(f"Consecutive errors: {self.consecutive_errors}")
        print(f"Total errors: {self.error_count}")

        # If we've hit max retries and enough time has passed since last reset
        if self.consecutive_errors >= self.MAX_RETRIES:
            if current_time - self.last_error_time > self.ERROR_TIMEOUT:
                print("Attempting sensor reset and recalibration...")
                try:
                    self.reset_and_recalibrate()
                    self.consecutive_errors = 0  # Only reset if successful
                    self.last_error_time = current_time
                    return
                except Exception as e:
                    print(f"Reset failed: {e}")

            # If we get here, either the timeout hasn't passed or reset failed
            raise SensorError(f"Too many consecutive errors: {error_msg}")

        time.sleep(self.RETRY_DELAY)

    def _wait_not_busy(self):
        """Wait until the detector is not busy."""
        if DEBUG:
            print("\nWaiting for detector not busy...")

        attempts = 0
        while True:
            status = self._read_register(self.REG_DETECTOR_STATUS)
            if status is None:
                if DEBUG:
                    print("  Failed to read status")
                break

            busy = bool(status & self.DETECTOR_STATUS_BUSY_MASK)
            if DEBUG:
                print(f"  Status: 0x{status:08x}, Busy: {busy}")

            if not busy:
                break

            time.sleep(0.01)
            attempts += 1
            if attempts >= 100:  # Timeout after 1 second
                if DEBUG:
                    print("  Timeout waiting for not busy")
                break

    def begin(self, start_mm=250, end_mm=10000):
        """Initialize the sensor with given start and end distances in mm."""
        if DEBUG:
            print(f"\nInitializing sensor:")
            print(f"  Start distance: {start_mm}mm")
            print(f"  End distance: {end_mm}mm")
            print(f"  Reflector shape: {self.REFLECTOR_SHAPE}")

        # Configure start and end distances
        if not self._write_register(self.REG_START, start_mm):
            if DEBUG:
                print("Failed to set start distance")
            return False

        if not self._write_register(self.REG_END, end_mm):
            if DEBUG:
                print("Failed to set end distance")
            return False

        if not self._write_register(self.REG_REFLECTOR_SHAPE, self.REFLECTOR_SHAPE):
            if DEBUG:
                print("Failed to set reflector shape")
            return False

        if DEBUG:
            print("Applying configuration and calibrating...")

        # Apply configuration and calibrate
        if not self._write_register(self.REG_COMMAND, self.CMD_APPLY_CONFIG_AND_CALIBRATE):
            if DEBUG:
                print("Failed to apply configuration and calibrate")
            return False

        self._wait_not_busy()

        # Check status
        status = self._read_register(self.REG_DETECTOR_STATUS)
        if DEBUG:
            print(f"Final status: 0x{status:08x}" if status is not None else "Failed to read final status")

        return status is not None and status >= 0

    def reset_and_recalibrate(self):
        """Reset the sensor and recalibrate."""
        try:
            # Reset the module
            self._write_register(self.REG_COMMAND, self.CMD_RESET_MODULE)
            time.sleep(1.0)  # Wait for reset

            # Clear averaging buffers
            self.distance_avg.reset()
            self.strength_avg.reset()

            # Reinitialize
            if not self.begin():
                raise SensorError("Failed to reinitialize sensor after reset")

            print("Sensor reset and recalibration successful")
            self.state = SensorState.INITIALIZED

        except Exception as e:
            self.state = SensorState.ERROR
            raise SensorError(f"Reset and recalibration failed: {str(e)}")

    def check_calibration(self) -> bool:
        """Check if sensor needs calibration and perform if needed."""
        result = self._read_register(self.REG_DISTANCE_RESULT)
        if result is None:
            return False

        if result & self.DISTANCE_RESULT_CALIBRATION_NEEDED:
            print("Calibration needed, recalibrating...")
            self._write_register(self.REG_COMMAND, self.CMD_RECALIBRATE)
            time.sleep(0.5)
            self.state = SensorState.INITIALIZED
            return True

        return True

    def measure(self) -> List[Dict[str, Tuple[float, float]]]:
        """Perform a distance measurement with error checking and recovery."""
        try:
            if self.state == SensorState.ERROR:
                self.reset_and_recalibrate()

            if not self.check_calibration():
                return []

            # Start measurement
            if not self._write_register(self.REG_COMMAND, self.CMD_MEASURE_DISTANCE):
                return []

            self._wait_not_busy()

            # Read result
            result = self._read_register(self.REG_DISTANCE_RESULT)
            if result is None:
                return []

            if result & self.DISTANCE_RESULT_MEASURE_DISTANCE_ERROR:
                self._handle_error("Measurement error")
                return []

            num_distances = (result & self.DISTANCE_RESULT_NUM_DISTANCES_MASK)
            peaks_with_average = []

            for i in range(num_distances):
                distance = self._read_register(self.REG_PEAK0_DISTANCE + i)
                strength = self._read_register(self.REG_PEAK0_STRENGTH + i)

                if distance is not None and strength is not None:
                    # Convert strength from 32-bit unsigned to signed int
                    if strength > 0x7FFFFFFF:
                        strength = int(0x100000000 - strength)

                    self.distance_avg.add(distance)
                    self.strength_avg.add(strength)

                    peak_data = {
                        'raw': (distance, strength),
                        'averaged': (self.distance_avg.get_average(),
                                     self.strength_avg.get_average()) if self.distance_avg.is_valid() else None
                    }
                    peaks_with_average.append(peak_data)

            # Only reset consecutive errors if we got valid data
            if peaks_with_average:
                self.consecutive_errors = 0

            return peaks_with_average

        except Exception as e:
            self._handle_error(f"Measurement error: {str(e)}")
            return []


def main():
    sensor = XM125(average_window=5)

    try:
        if not sensor.begin():
            print("Failed to initialize sensor")
            return

        print("Sensor initialized successfully")

        while True:
            try:
                peaks = sensor.measure()

                if peaks:
                    for i, peak_data in enumerate(peaks):
                        raw_distance, raw_strength = peak_data['raw']
                        print(f"\nPeak {i}:")
                        print(f"  Raw: Distance = {raw_distance}mm, Strength = {raw_strength}")

                        if peak_data['averaged']:
                            avg_distance, avg_strength = peak_data['averaged']
                            print(f"  Avg: Distance = {avg_distance:.1f}mm, Strength = {avg_strength:.1f}")
                else:
                    print("No peaks detected")

                time.sleep(0.5)

            except SensorError as e:
                print(f"Sensor error: {e}")
                print("Waiting before retry...")
                time.sleep(2.0)  # Longer delay on serious errors

                # Try to reset the sensor on serious errors
                try:
                    sensor.reset_and_recalibrate()
                except Exception as reset_error:
                    print(f"Reset failed: {reset_error}")
                    time.sleep(5.0)  # Even longer delay if reset fails

    except KeyboardInterrupt:
        print("\nStopping measurements")
        sensor.bus.close()
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
