import time
from src.modules.imaging.camera import RPiCamera
from src.modules.imaging.mavlink import MAVLinkDelegate
from src.modules.imaging.location import MAVLinkLocationProvider

CONN_STR = "tcp:127.0.0.1:14550"
MESSENGER_PORT = 14552


# NOTE: MAKE SURE THE CAMERA WITHOUT IR FILTER IS CONNECTED TO CAMERA 1
cam = RPiCamera(1)
#mavlink = MAVLinkDelegate()

drone = connect(CONN_STR, wait_read=False)

os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs)
os.makedirs(f"tmp/log/{ft_num}")  # no exist_ok bc. this folder should be new

i = 0
last_picture = time.time()

def take_picture(_):
    global i
    global last_picture

    cam.caputure_to(f"tmp/log/{ft_num}/{i}.png")
    print(i)
    i += 1

def picture_loop(sleep):
    while True:
        take_picture(None)
        time.sleep(sleep)
picture_loop(2)



