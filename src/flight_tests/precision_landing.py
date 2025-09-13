from src.modules.imaging.analysis import AnalysisDelegate
from src.modules.mavctl.mavctl.connect import conn
from pymavlink import mavutil
from src.modules.mavctl.mavctl.messages.Navigator import Navigator
from src.modules.mavctl.mavctl.messages.messenger import Messenger
from src.modules.mavctl.mavctl.messages import advanced

CONN_STR = "udp:127.0.0.1:14551"

mav = conn.connect()
master = Navigator(mav)
master.send_status_message("MAVCTL: Online")

imaging_analysis_delegate = AnalysisDelegate
