import math
from src.modules.imaging.mavlink import MAVLinkDelegate
import pymavlink.dialects.v20.all as dialect


class BatteryStatusProvider:
    """
    Provides the current status of the drone's battery / power usage.
    """

    def voltage(self) -> float:
        """
        Get the latest voltage of the drone batter in Volts.
        """
        raise NotImplementedError()


class DebugBatteryStatusProvider(BatteryStatusProvider):
    """
    For testing / debugging
    """

    def __init__(self) -> None:
        self._current_voltage = 0

    def voltage(self) -> float:
        return self._current_voltage

    def set_voltage(self, new_voltage):
        self._current_voltage = new_voltage


class MAVLinkBatteryStatusProvider:
    """
    For use in production when a MAVLink connection is available.
    """

    def __init__(self, mavlink_delegate: MAVLinkDelegate):
        self.mavlink_delegate = mavlink_delegate
        self._voltage: Optional[float] = None

        # Subscribe to the delegate's messages
        self.mavlink_delegate.subscribe(self._process_message)
        self.mavlink_delegate.send(
                dialect.MAVLink_command_long_message(
                    target_system=1,
                    target_component=1,
                    command=dialect.MAV_CMD_SET_MESSAGE_INTERVAL,
                    confirmation=0,
                    param1=1,       # param1: send SYS_STATUS message
                    param2=500000,  # param2: send every 5e5 us
                    param3=0,
                    param4=0,
                    param5=0,
                    param6=0,
                    param7=1))      # param7: send messaged to requester

    def _process_message(self, message):
        # This callback processes incoming MAVLink messages and updates the internal state
        if message.get_type() == 'SYS_STATUS':
            # message.voltage_battery is an int in mV
            self._voltage = float(message.voltage_battery) / 1e3

    def voltage(self) -> float:
        if self._voltage is not None:
            return self._voltage
        else:
            raise ValueError("No valid voltage data available")
