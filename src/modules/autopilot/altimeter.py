import smbus2
import time


DEBUG = False


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


class XM125:
    # Register addresses from documentation
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

    # Value enums
    REFLECTOR_SHAPE = 1  # 1 = Generic, 2 = Planar

    # Status masks
    DETECTOR_STATUS_BUSY_MASK = 0x80000000
    DISTANCE_RESULT_NUM_DISTANCES_MASK = 0x0000000f
    DISTANCE_RESULT_NEAR_START_EDGE = 0x00000100
    DISTANCE_RESULT_CALIBRATION_NEEDED = 0x00000200
    DISTANCE_RESULT_MEASURE_DISTANCE_ERROR = 0x00000400

    def __init__(self, bus=1, address=0x52, average_window=5):
        self.bus = smbus2.SMBus(bus)
        self.address = address
        self.distance_avg = MovingAverage()
        self.strength_avg = MovingAverage()

    def _read_register(self, reg_addr):
        """Read a 32-bit register value."""
        try:
            # Write register address (big endian)
            write = smbus2.i2c_msg.write(self.address, [(reg_addr >> 8) & 0xFF, reg_addr & 0xFF])
            read = smbus2.i2c_msg.read(self.address, 4)

            if DEBUG:
                print(f"\nREAD OPERATION:")
                print(f"  Register: 0x{reg_addr:04x}")
                print(f"  Sending address bytes: MSB=0x{(reg_addr >> 8) & 0xFF:02x}, LSB=0x{reg_addr & 0xFF:02x}")

            # Execute the transaction with repeated start
            self.bus.i2c_rdwr(write, read)

            # Convert the read result to bytes
            data = list(read)

            # Convert to 32-bit integer (big endian as per protocol)
            value = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

            if DEBUG:
                print(f"  Received bytes: [0x{data[0]:02x}, 0x{data[1]:02x}, 0x{data[2]:02x}, 0x{data[3]:02x}]")
                print(f"  Decoded value: 0x{value:08x} ({value})")

            return value
        except IOError as e:
            print(f"I/O error reading register 0x{reg_addr:04x}: {e}")
            return None

    def _write_register(self, reg_addr, value):
        """Write a 32-bit register value."""
        try:
            # Prepare all 6 bytes as per protocol example
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
                print(
                    f"  Sending bytes: [0x{data[0]:02x}, 0x{data[1]:02x}, 0x{data[2]:02x}, 0x{data[3]:02x}, 0x{data[4]:02x}, 0x{data[5]:02x}]")

            # Write all bytes in a single transaction
            self.bus.write_i2c_block_data(self.address, data[0], data[1:])
            return True
        except IOError as e:
            print(f"I/O error writing register 0x{reg_addr:04x}: {e}")
            return False

    def wait_not_busy(self):
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

    def begin(self, start_mm=250, end_mm=3000):
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

        self.wait_not_busy()

        # Check status
        status = self._read_register(self.REG_DETECTOR_STATUS)
        if DEBUG:
            print(f"Final status: 0x{status:08x}" if status is not None else "Failed to read final status")

        return status is not None and status >= 0

    def measure(self):
        """Perform a distance measurement and return the results."""
        if DEBUG:
            print("\nStarting measurement...")

        # Start measurement
        if not self._write_register(self.REG_COMMAND, self.CMD_MEASURE_DISTANCE):
            if DEBUG:
                print("Failed to start measurement")
            return []

        self.wait_not_busy()

        # Read result
        result = self._read_register(self.REG_DISTANCE_RESULT)
        if result is None:
            if DEBUG:
                print("Failed to read measurement result")
            return []

        if DEBUG:
            print(f"Measurement result: 0x{result:08x}")

        if result & self.DISTANCE_RESULT_MEASURE_DISTANCE_ERROR:
            print("Error: Measurement error")
            return []

        if result & self.DISTANCE_RESULT_CALIBRATION_NEEDED:
            print("Error: Calibration needed")
            return []

        num_distances = (result & self.DISTANCE_RESULT_NUM_DISTANCES_MASK)

        if DEBUG:
            print(f"Number of distances detected: {num_distances}")

        peaks_with_average = []

        for i in range(num_distances):
            if DEBUG:
                print(f"\nReading peak {i}:")

            distance = self._read_register(self.REG_PEAK0_DISTANCE + i)
            strength = self._read_register(self.REG_PEAK0_STRENGTH + i)

            if distance is not None and strength is not None:
                # Add to moving averages
                self.distance_avg.add(distance)
                self.strength_avg.add(strength)

                # Create tuple with both raw and averaged values
                avg_distance = self.distance_avg.get_average()
                avg_strength = self.strength_avg.get_average()

                peak_data = {
                    'raw': (distance, strength),
                    'averaged': (avg_distance, avg_strength) if self.distance_avg.is_valid() else None
                }

                peaks_with_average.append(peak_data)

                if DEBUG:
                    print(f"  Raw Distance: {distance}mm, Strength: {strength}")
                    if self.distance_avg.is_valid():
                        print(f"  Avg Distance: {avg_distance:.1f}mm, Strength: {avg_strength:.1f}")

        return peaks_with_average


def main():
    # Initialize sensor
    sensor = XM125(average_window=5)  # 5-sample moving average

    try:
        # Setup sensor with 1m to 5m range
        if not sensor.begin(start_mm=1000, end_mm=5000):
            print("Failed to initialize sensor")
            return

        print("Sensor initialized successfully")

        # Continuous measurement loop
        while True:
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

    except KeyboardInterrupt:
        print("\nStopping measurements")
        sensor.bus.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
