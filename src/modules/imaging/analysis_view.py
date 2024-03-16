from mavlink import MAVLinkDelegate
import pymavlink.dialects.v20.all as dialect
from dep.labeller.benchmarks.detector import BoundingBox


class AnalysisView:
    """
    Sends debugging messages to ground station through mavlink protocol.
    """

    def __init__(self, mavlinkDelegate: MAVLinkDelegate) -> None:
        self.mavlink = mavlinkDelegate

    def send_BoundingBox(self, bbox: BoundingBox) -> None:
        position = bbox.position
        size = bbox.size
        values = [position.x, position.y, size.x, size.y]
        for i in range(4, 58):
            values[i] = 0.0

        dbg_box = dialect.MAVLink_debug_float_array_message(
            name=bytes("dbg_box", 'utf-8'),
            time_usec=0,  # timestamp
            array_id=0,
            data=values)
        self.mavlink.send(dbg_box)
