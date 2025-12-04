from src.modules.mavctl.mavctl.connect import conn
from src.modules.mavctl.mavctl.messages.navigator import Navigator
import time

CONN_STR = "udp:127.0.0.1:14550"

mav = conn.Connect(ip = CONN_STR)
master = Navigator(mav.mav)

while True:
    pos = master.get_local_position()
    print(pos.north,  pos.east, pos.down)
    time.sleep(0.5)
