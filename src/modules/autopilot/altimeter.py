import smbus2
import time


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
    REFLECTOR_SHAPE = 2  # 1 = Generic, 2 = Planar

    # Status masks
    DETECTOR_STATUS_BUSY_MASK = 0x80000000
    DISTANCE_RESULT_NUM_DISTANCES_MASK = 0x0000000f

    def __init__(self, bus=1, address=0x52):
        self.bus = smbus2.SMBus(bus)
        self.address = address

    def _read_register(self, reg_addr):
        """Read a 32-bit register value."""
        try:
            # Write register address (big endian)
            msb = (reg_addr >> 8) & 0xFF  # Address to slave [15:8]
            lsb = reg_addr & 0xFF         # Address to slave [7:0]
            self.bus.write_i2c_block_data(self.address, msb, [lsb])

            # Read 4 bytes
            data = self.bus.read_i2c_block_data(self.address, 0, 4)

            # Convert to 32-bit integer (big endian as per protocol)
            value = (data[0] << 24) | (
                data[1] << 16) | (data[2] << 8) | data[3]
            return value
        except IOError as e:
            print(f"I/O error reading register 0x{reg_addr:04x}: {e}")
            return None

    def _write_register(self, reg_addr, value):
        """Write a 32-bit register value."""
        try:
            # Prepare all 6 bytes as per protocol example:
            # Address [15:8], Address [7:0], Data [31:24], Data [23:16], Data [15:8], Data [7:0]
            data = [
                (reg_addr >> 8) & 0xFF,    # Address to slave [15:8]
                reg_addr & 0xFF,           # Address to slave [7:0]
                (value >> 24) & 0xFF,      # Data to slave [31:24]
                (value >> 16) & 0xFF,      # Data to slave [23:16]
                (value >> 8) & 0xFF,       # Data to slave [15:8]
                value & 0xFF               # Data to slave [7:0]
            ]
            # Write all bytes in a single transaction
            self.bus.write_i2c_block_data(self.address, data[0], data[1:])
            return True
        except IOError as e:
            print(f"I/O error writing register 0x{reg_addr:04x}: {e}")
            return False

    def wait_not_busy(self):
        """Wait until the detector is not busy."""
        while True:
            status = self._read_register(self.REG_DETECTOR_STATUS)
            if status is None or not (status & self.DETECTOR_STATUS_BUSY_MASK):
                break
            time.sleep(0.01)

    def begin(self, start_mm=1000, end_mm=5000):
        """Initialize the sensor with given start and end distances in mm."""
        # Configure start and end distances
        if not self._write_register(self.REG_START, start_mm):
            return False

        if not self._write_register(self.REG_END, end_mm):
            return False

        if not self._write_register(self.REG_REFLECTOR_SHAPE, self.REFLECTOR_SHAPE):
            return False

        # Apply configuration and calibrate
        if not self._write_register(self.REG_COMMAND, self.CMD_APPLY_CONFIG_AND_CALIBRATE):
            return False

        self.wait_not_busy()

        # Check status
        status = self._read_register(self.REG_DETECTOR_STATUS)
        return status is not None and status >= 0

    def measure(self):
        """Perform a distance measurement and return the results."""
        # Start measurement
        if not self._write_register(self.REG_COMMAND, self.CMD_MEASURE_DISTANCE):
            return []

        self.wait_not_busy()

        # Read result
        result = self._read_register(self.REG_DISTANCE_RESULT)
        if result is None:
            return []

        num_distances = (result & self.DISTANCE_RESULT_NUM_DISTANCES_MASK)

        peaks = []
        for i in range(num_distances):
            distance = self._read_register(self.REG_PEAK0_DISTANCE + i)
            strength = self._read_register(self.REG_PEAK0_STRENGTH + i)
            if distance is not None and strength is not None:
                peaks.append((distance, strength))

        return peaks


def main():
    # Initialize sensor
    sensor = XM125()

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
                for i, (distance, strength) in enumerate(peaks):
                    print(f"Peak {i}: Distance = {distance}mm, Strength = {strength}")
            else:
                print("No peaks detected")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nStopping measurements")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
