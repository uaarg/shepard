from pymavlink import mavutil
import pymavlink.dialects.v20.all as dialect


class Messenger:
    """
    Messenger class for sending messages from the autopilot to the ground station.

    Source:
    https://github.com/mustafa-gokce/ardupilot-software-development/blob/main/pymavlink/send-status-text.py
    """

    def __init__(self, port):
        self.__master = mavutil.mavlink_connection(
            device=f"udp:127.0.0.1:{port}",
            source_system=1,
            source_component=1)

    def send(self, message):
        """
        Sends a message to the ground station.

        :param message: The message to send.
        :return: None
        """

        mav_message = dialect.MAVLink_statustext_message(
            severity=dialect.MAV_SEVERITY_INFO, text=message.encode("utf-8"))
        self.__master.mav.send(mav_message)
