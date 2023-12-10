from pymavlink import mavutil


class Messenger:
    """
    Messenger class for sending messages from the autopilot to the ground station.
    """

    def __init__(self, conn_str):
        self.__master = None
        self.connect(conn_str)

    def connect(self, conn_str):
        """
        Connects to the ground station.

        :param conn_str: The connection string.
        :return: None
        """

        self.__master = mavutil.mavlink_connection(conn_str)

        self.__master.wait_heartbeat()
        print("Heartbeat from system (system %u component %u)" %
              (self.__master.target_system, self.__master.target_component))

    def send(self, message):
        """
        Sends a message to the ground station.

        :param message: The message to send.
        :return: None
        """

        self.__master.mav.statustext_send(mavutil.mavlink.MAV_SEVERITY_INFO, message)
