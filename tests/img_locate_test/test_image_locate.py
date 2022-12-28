"""
Unit Testing for Object Location Determination

This unit test verifies that our code can determine the GPS coordinates of 
a object based on the GPS position of the camera and the camera angle
"""

import unittest
import sys

from pathlib import Path
FILE = Path(__file__).resolve()
ROOT = FILE.parents[2]
if (str(ROOT)) not in sys.path:
    sys.path.append(str(ROOT))  # add root directory to PATH
    
from image_analysis.inference_georeference import calculate_object_offsets

class TestImageLocate(unittest.TestCase):

    def test_zero_orientation(self):
        """
        This test has the object of interest directly below the drone
        
        Expected output is the same coordinates as the drone
        The test verifies the base functionality
        """

        x_offset, y_offset = calculate_object_offsets(height=10, pitch=0, roll=0, yaw=180, x=0.5, y=0.5)

        self.assertAlmostEqual(x_offset, 0, places=5)
        self.assertAlmostEqual(y_offset, 0, places=5)
    
    def test_forward_image(self):
        """
        This test has the object in front of the drone with camera directly down
        
        Expected output is about 2m north of the drone (drone faces north)
        Verifies that the y distance is orientated correctly
        """

        x_offset, y_offset = calculate_object_offsets(height=10, pitch=0, roll=0, yaw=0, x=0.5, y=0.25)

        self.assertAlmostEqual(x_offset, 0, places=5)
        self.assertAlmostEqual(y_offset, 2.211920356, places=5)

    def test_right_image(self):
        """
        This test has the object to the right of the drone with camera directly down
        
        Expected output is about 2m east of the drone (drone faces north)
        Verifies that the x distance is orientated correctly
        """

        x_offset, y_offset = calculate_object_offsets(height=10, pitch=0, roll=0, yaw=0, x=0.75, y=0.50)

        self.assertAlmostEqual(x_offset, 2.887698619, places=5)
        self.assertAlmostEqual(y_offset, 0, places=5)
    
    def test_forward_image_yaw(self):
        """
        This test has the object in front of the drone with camera directly down
        
        Expected output is about 2m east of the drone (drone faces East)
        This test verifies that yaw is orientated correctly
        """

        x_offset, y_offset = calculate_object_offsets(height=10, pitch=0, roll=0, yaw=90, x=0.5, y=0.25)

        self.assertAlmostEqual(x_offset, 2.211920356, places=5)
        self.assertAlmostEqual(y_offset, 0, places=5)

    def test_img_pitch(self):
        """
        This test has the object in front of the camera with camera pitched up
        
        Expected output is about 2m north of the drone (drone faces North)
        This test verifies that pitch is orientated correctly
        """

        x_offset, y_offset = calculate_object_offsets(height=10, pitch=15, roll=0, yaw=0, x=0.5, y=0.5)

        self.assertAlmostEqual(x_offset, 0, places=5)
        self.assertAlmostEqual(y_offset, 2.679491924, places=5)

    def test_img_roll(self):
        """
        This test has the object in front of the camera with camera pitched up
        
        Expected output is about 2m north of the drone (drone faces North)
        This test verifies that roll is orientated correctly
        """

        x_offset, y_offset = calculate_object_offsets(height=10, pitch=0, roll=15, yaw=0, x=0.5, y=0.5)

        self.assertAlmostEqual(x_offset, 2.679491924, places=5)
        self.assertAlmostEqual(y_offset, 0, places=5)

    def test_error_handle(self):
        """
        This test puts the object detected above the horizon

        This test makes sure that our application wont crash and simply drops
        the detection instead
        """

        x_offset, y_offset = calculate_object_offsets(height=10, pitch=0, roll=100, yaw=0, x=0.5, y=0.5)

        self.assertEqual(x_offset, None)
        self.assertEqual(y_offset, None)

if __name__ == '__main__':
    unittest.main()