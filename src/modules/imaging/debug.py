from PIL import Image

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

    def show(self):
        """
        Start displaying the debugger window.
        """
        raise NotImplementedError()

    def hide(self):
        """
        Stop displaying the debugger window.
        """
        raise NotImplementedError()

    def visible(self) -> bool:
        """
        Returns True if the debug window is visible.
        False if it is no longer visible because:
        - show() has not been called
        - hide() was called
        - the user closed the window
        """
        raise NotImplementedError()

    def set_image(self, image: Image.Image):
        """
        Update the image currently being analysed. Will remove any old bounding boxes.
        """
        raise NotImplementedError()

    def set_bounding_box(self, bb: BoundingBox):
        """
        Update the bounding box currently displaying the image being debugged.
        """
        raise NotImplementedError()
