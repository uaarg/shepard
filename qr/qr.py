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

    if (decoded_text != ""):
        print(decoded_text)
    else:
        print("No text decoded. This may mean the QR code could not be read in the image. Try again with a different image.")
        return 1


if __name__ == "__main__":
    readQRCode(IMAGE_PATH)

