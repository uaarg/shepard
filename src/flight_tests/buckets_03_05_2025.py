'''
take photos with a certain interval
'''
import os
import time
from src.modules.imaging.camera import RPiCamera

interval = 0.25 # quarter second between photos

os.makedirs("tmp/log", exist_ok=True)
dirs = os.listdir("tmp/log")
ft_num = len(dirs)

cam = RPiCamera(0)

i = 0
while True:
    path = f"tmp/log/{ft_num}/{i}.png"
    cam.caputure_to(path)

    time.sleep(interval)
    i += 1
