from PIL import Image, ImageOps
import time

from src.modules.imaging.debug import ImageAnalysisDebugger
from benchmarks.detector import BoundingBox, Vec2

im = Image.open("res/test-image.jpeg")
bb = BoundingBox(Vec2(200, 120), Vec2(100, 100))

dbg = ImageAnalysisDebugger()
print("The debugger should not be visible right now.")

dbg.set_image(im)
dbg.set_bounding_box(bb)

dbg.show()
print("The debugger should now be visible")

print("Because the debugger is not blocking, we can continue to run code.")
print("Close the window to stop")
for i in range(10):
    print(f"Running {10 - i} more times")
    print("Flipping image")
    im = ImageOps.flip(im.copy())
    bb.position = Vec2(bb.position.x, im.height - bb.position.y)

    dbg.set_image(im)

    print("Waiting 1s to display bounding box")
    time.sleep(1)

    dbg.set_bounding_box(bb)
    dbg.show()

    print("Waiting 2s to display new image")
    time.sleep(2)

print("Before you go! Look at the image for another 3s")
dbg.show()
time.sleep(3)

print("Bye! (Should exit the program now)")
