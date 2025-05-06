from typing import Optional

from PIL import Image, ImageDraw
import numpy as np
import cv2

from dep.labeller.loader import Vec2
from dep.labeller.benchmarks.detector import BoundingBox, LandingPadDetector



class IrDetector(LandingPadDetector):

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        img = np.array(image)

        gray_img = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
        max_val = np.max(gray_img) # returns maximum value of brightness 
        if max_val < 200: return None #lower threshold for intensity 
        _, thresh = cv2.threshold(gray_img, max_val - 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        #output = cv2.drawContours(thresh, contours, -1, (0, 255, 0), 2)

        if len(contours) == 0: return None

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

        return BoundingBox(Vec2(x, y), Vec2(w, h))


class InvertedIrDetector(IrDetector):

    def predict(self, image: Image.Image) -> Optional[BoundingBox]:
        return super().predict(Image.fromarray(255 - np.array(image)))


if __name__ == "__main__":
    # Helper, run with `PYTHONPATH=. python3 path/to/detector.py --invert image.png`

    import argparse

    parser = argparse.ArgumentParser()
    parser.description = 'Detect IR hotspots in a test image'
    parser.add_argument('image', help="Image to process")
    parser.add_argument('--invert', action='store_true', help="Invert the image before checking for hotspots")
    args = parser.parse_args()

    detector = IrDetector()
    im = Image.open(args.image).convert("RGB")

    if args.invert:
        # Max val is 255 per channel per pixel
        detector = InvertedIrDetector()

    bb = detector.predict(im)
    if bb is None:
        print("No IR source detected")
    else:
        draw = ImageDraw.Draw(im)
        draw.ink = 0xFF00FF
        draw.rectangle((bb.position.x, bb.position.y,
                        bb.position.x + bb.size.x, bb.position.y + bb.size.y))
        im.show()
