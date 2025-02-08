import smbus2
import time

DEBUG = True

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
    DISTANCE_RESULT_NEAR_START_EDGE = 0x00000100
    DISTANCE_RESULT_CALIBRATION_NEEDED = 0x00000200
    DISTANCE_RESULT_MEASURE_DISTANCE_ERROR = 0x00000400

    def __init__(self, bus=1, address=0x52):
        self.bus = smbus2.SMBus(bus)
        self.address = address
        if DEBUG:
            print(f"Initialized XM125 with bus={bus} and address=0x{address:02x}")

    def _read_register(self, reg_addr):
        """Read a 32-bit register value."""
        try:
            msb = (reg_addr >> 8) & 0xFF
            lsb = reg_addr & 0xFF

            if DEBUG:
                print(f"Reading register 0x{reg_addr:04x}")

            self.bus.write_i2c_block_data(self.address, msb, [lsb])
            data = self.bus.read_i2c_block_data(self.address, 0, 4)
            value = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

            if DEBUG:
                print(f"Read value 0x{value:08x} from register 0x{reg_addr:04x}")

            return value
        except IOError as e:
            print(f"I/O error reading register 0x{reg_addr:04x}: {e}")
            return None

    def _write_register(self, reg_addr, value):
        """Write a 32-bit register value."""
        try:
            data = [
                (reg_addr >> 8) & 0xFF,
                reg_addr & 0xFF,
                (value >> 24) & 0xFF,
                (value >> 16) & 0xFF,
                (value >> 8) & 0xFF,
                value & 0xFF
            ]

            if DEBUG:
                print(f"Writing value 0x{value:08x} to register 0x{reg_addr:04x}")

            self.bus.write_i2c_block_data(self.address, data[0], data[1:])
            return True
        except IOError as e:
            print(f"I/O error writing register 0x{reg_addr:04x}: {e}")
            return False

    def wait_not_busy(self):
        """Wait until the detector is not busy."""
        if DEBUG:
            print("Waiting for detector to be not busy")
        while True:
            status = self._read_register(self.REG_DETECTOR_STATUS)
            if status is None or not (status & self.DETECTOR_STATUS_BUSY_MASK):
                break
            time.sleep(0.01)
        if DEBUG:
            print("Detector is not busy")

    def begin(self, start_mm=1000, end_mm=5000):
        """Initialize the sensor with given start and end distances in mm."""
        if DEBUG:
            print(f"Initializing sensor with start_mm={start_mm} and end_mm={end_mm}")

        if not self._write_register(self.REG_START, start_mm):
            return False

        if not self._write_register(self.REG_END, end_mm):
            return False

        if not self._write_register(self.REG_REFLECTOR_SHAPE, self.REFLECTOR_SHAPE):
            return False

        if not self._write_register(self.REG_COMMAND, self.CMD_APPLY_CONFIG_AND_CALIBRATE):
            return False

        self.wait_not_busy()

        status = self._read_register(self.REG_DETECTOR_STATUS)
        if DEBUG:
            print(f"Initialization status: {status}")

        return status is not None and status >= 0

    def measure(self):
        """Perform a distance measurement and return the results."""
        if DEBUG:
            print("Starting distance measurement")

        if not self._write_register(self.REG_COMMAND, self.CMD_MEASURE_DISTANCE):
            return []

        self.wait_not_busy()

        result = self._read_register(self.REG_DISTANCE_RESULT)
        if result is None:
            return []

        if result & self.DISTANCE_RESULT_MEASURE_DISTANCE_ERROR:
            print("Error: Measurement error")
            return []

        if result & self.DISTANCE_RESULT_CALIBRATION_NEEDED:
            print("Error: Calibration needed")
            return []

        if result & self.DISTANCE_RESULT_NEAR_START_EDGE:
            print("Warning: Near start edge")
            return []

        num_distances = (result & self.DISTANCE_RESULT_NUM_DISTANCES_MASK)

        if DEBUG:
            print(f"Number of distances: {num_distances}")

        peaks = []
        for i in range(num_distances):
            distance = self._read_register(self.REG_PEAK0_DISTANCE + i)
            strength = self._read_register(self.REG_PEAK0_STRENGTH + i)
            if distance is not None and strength is not None:
                peaks.append((distance, strength))
                if DEBUG:
                    print(f"Peak {i}: Distance = {distance}mm, Strength = {strength}")

        return peaks

def main():
    sensor = XM125()

    try:
        if not sensor.begin(start_mm=1000, end_mm=5000):
            print("Failed to initialize sensor")
            return

        print("Sensor initialized successfully")

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
        sensor.bus.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
