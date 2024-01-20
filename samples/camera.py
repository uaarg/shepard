# Test the WebcamCamera class

import time
import sys

from src.modules.imaging.camera import WebcamCamera

cam = RPiCamera()

cam.set_size((1000, 1000))

print("Taking a picture in 3s.")

for i in reversed(range(3)):
    print(f"{i + 1} ", end="")
    # stdout is linebuffered, so nothing will print until a \n otherwise
    sys.stdout.flush()

    time.sleep(1)

print("\rSay cheese!")
time.sleep(1)

cam.caputure_to("tmp/you.png")
print("Image saved to tmp/you.png")
