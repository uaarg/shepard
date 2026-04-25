from PIL import Image, ImageDraw
import os
from typing import Optional, Tuple

from src.modules.emu import Emu
from src.modules.imaging.detector import BoundingBox


class ArucoEmuStreamer:
    def __init__(self, emu: Emu, output_dir: str = "tmp"):
        self.emu = emu
        self.output_dir = output_dir
        self.counter = 0

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def on_detection(self, image: Image.Image, bounding_box: Optional[BoundingBox], position: Optional[Tuple[float, float]]):
        im = image.copy()
        
        if bounding_box is not None:
            draw = ImageDraw.Draw(im)
            bb = (bounding_box.position.x, bounding_box.position.y,
                  bounding_box.position.x + bounding_box.size.x, 
                  bounding_box.position.y + bounding_box.size.y)
            draw.rectangle(bb, outline="red")
            
        filename = f"{self.counter}.jpeg"
        filepath = os.path.join(self.output_dir, filename)
        im.save(filepath)
        
        self.emu.send_image(filename)
        self.counter += 1
