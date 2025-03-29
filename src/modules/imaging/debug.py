from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageTk
import tkinter as tk
from dep.labeller.benchmarks.detector import BoundingBox


class ImageAnalysisDebugger:
    """
    Helper class to display a debug window containing image analysis results.

    Note, all methods are non-blocking. This means, ie. calling show() will not
    block the program until the window is closed. This debugger will run in the
    background and should not interfere in any way.
    """

    def __init__(self):
        self.image: Optional[Image.Image] = None
        self.root = tk.Tk()
        self.is_visible = False

    def show(self):
        """
        Start displaying the debugger window.
        """
        if not self.image:
            raise RuntimeError("No image set. Cannot show without an image")

        self.root.deiconify()
        self.is_visible = True
        img = ImageTk.PhotoImage(self.image)
        self.root.geometry('%dx%d' % (self.image.size[0], self.image.size[1]))
        label_image = tk.Label(self.root, image=img)
        label_image.place(x=0,
                          y=0,
                          width=self.image.size[0],
                          height=self.image.size[1])
        self.root.update()

    def hide(self):
        """
        Stop displaying the debugger window.
        """
        self.root.withdraw()
        self.is_visible = False

    def visible(self) -> bool:
        """
        Returns True if the debug window is visible.
        False if it is no longer visible because:
        - show() has not been called
        - hide() was called
        - the user closed the window
        """
        return self.is_visible

    def set_image(self, image: Image.Image):
        """
        Update the image currently being analysed. Will remove any old bounding boxes.
        """
        self.image = image.copy()

    def set_bounding_box(self, bb: BoundingBox):
        """
        Update the bounding box currently displaying the image being debugged.
        """
        if not self.image:
            return  # return no image set error

        image = self.image
        top_left_corner: Tuple[float, float] = (bb.position.x, bb.position.y)
        bottom_right_corner: Tuple[float, float] = (bb.position.x + bb.size.x,
                                                    bb.position.y + bb.size.y)

        draw = ImageDraw.Draw(image)
        draw.rectangle((top_left_corner, bottom_right_corner))
