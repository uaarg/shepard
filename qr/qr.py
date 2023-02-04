"""
    Given an image of a QR code, get and print raw text.
"""

import cv2
import math
import sys


IMAGE_PATH = "None"

# get image path passed in as argument from cli
if len(sys.argv) != 2:
    print(f"""
        INVALID USAGE. Specify a path to image of QR code. 
    """)
else:
    IMAGE_PATH = sys.argv[1]


def readQRCode(image):
    img = cv2.imread(image)

    QRCodeDetector = cv2.QRCodeDetector()
    decoded_text, _, _ = QRCodeDetector.detectAndDecode(img)

    print(decoded_text)


if __name__ == "__main__":
    readQRCode(IMAGE_PATH)

