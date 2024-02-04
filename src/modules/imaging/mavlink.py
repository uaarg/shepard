from typing import Callable

from pymavlink import mavutil
import pymavlink.dialects.v20.all as dialect
import time


class MAVLinkDelegate:
    """
    MAVLink connection delegate which forwards messages to subscribers.
    """

    def __init__(self, port: int = 14550):
        self._conn = mavutil.mavlink_connection(device=f"tcp:127.0.0.1:{port}",
                                                source_system=1,
                                                source_component=1)

        self._listeners = []

    def subscribe(self, listener: Callable):
        """
        Subscribe to messages received from the mavlink connection.
        """
        self._listeners.append(listener)

    def send(self, mav_message: dialect.MAVLink_message):
        """
        Sends a mavlink message.
        """
        self._conn.mav.send(mav_message)

    def run(self):
        """
        Start the mavlink delegate. Will never return.
        """
        while True:
            msg = self._conn.recv_match(blocking=False)
            if msg:
                for listener in self._listeners:
                    listener(msg)

                continue  # Check for more messages immediately

            time.sleep(0.0001)  # 100 us


class MAVLinkDelegateMock(MAVLinkDelegate):
    """
    Mock MAVLink connection delegate which forwards messages to subscribers.
    """

    def __init__(self):
        self._listeners = []

    def send(self, mav_message: dialect.MAVLink_message):
        """
        Sends a mavlink message.
        """
        for listener in self._listeners:
            listener(mav_message)

    def run(self):
        """
        Not implemented
        """
        raise AssertionError("Not implemented")


class MessagePrinter:

    def __init__(self, mavlink_delegate: MAVLinkDelegate):
        self.mavlink_delegate = mavlink_delegate
        self.mavlink_delegate.subscribe(self._process_message)

    def _process_message(self, message: dialect.MAVLink_message):
        print(message)


if __name__ == "__main__":
    mavlink_delegate = MAVLinkDelegate()
    message_printer = MessagePrinter(mavlink_delegate)
    print("Starting mavlink_delegate.run()")
    mavlink_delegate.run()
