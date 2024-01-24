from PIL import Image, ImageDraw
import cv2 as cv
import numpy as np
from benchmarks.detector import BoundingBox


class ImageAnalysisDebugger:
    """
    Helper class to display a debug window containing image analysis results.

    Note, all methods are non-blocking. This means, ie. calling show() will not
    block the program until the window is closed. This debugger will run in the
    background and should not interfere in any way.
    """

    def __init__(self):
        pass
        self.image = None
        self.temp_image = None

    def show(self):
        """
        Start displaying the debugger window.
        """
        cv.imshow("Image", np.array(self.temp_image))
        cv.waitKey(1)

    # def hide(self):
    #     """
    #     Stop displaying the debugger window.
    #     """
    #     pass

    # def visible(self) -> bool:
    #     """
    #     Returns True if the debug window is visible.
    #     False if it is no longer visible because:
    #     - show() has not been called
    #     - hide() was called
    #     - the user closed the window
    #     """
    #     # raise NotImplementedError()
    #     return True

    def set_image(self, image: Image.Image):
        """
        Update the image currently being analysed. Will remove any old bounding boxes.
        """

        self.image = image
        self.temp_image = image.copy()

    def set_bounding_box(self, bb: BoundingBox):
        """
        Update the bounding box currently displaying the image being debugged.
        """
        if not self.image:
            return  # return no image set error

        image = self.temp_image
        top_left_corner = (bb.position.x, bb.position.y)
        bottom_right_corner = (bb.position.x + bb.size.x,
                               bb.position.y + bb.size.y)

        draw = ImageDraw.Draw(image)
        draw.rectangle([top_left_corner, bottom_right_corner])
