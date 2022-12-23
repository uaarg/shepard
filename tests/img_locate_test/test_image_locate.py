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
    
from image_analysis.inference_georeference import get_inference_location

class TestImageLocate(unittest.TestCase):

    def test_directly_below(self):
        """
        This test has the object of interest directly below the drone
        
        Expected output is the same coordinates as the drone
        """

        inference = {'type': 'blue landing pad', 'confidence': 1, 'x': 0.5, 'y': 0.5, 'w': 0.2, 'h': 0.2}

        lon, lat = get_inference_location(str(FILE.parent) + "/0.png", inference)

        self.assertAlmostEqual(lat, 53.5121370)
        self.assertAlmostEqual(lon, -113.5491390)
    
    def test_forward_image(self):
        """
        This test has the object of interest in front of the drone
        
        Expected output is about 2m north of the drone (drone faces north)
        """

        inference = {'type': 'blue landing pad', 'confidence': 1, 'x': 0.5, 'y': 0.25, 'w': 0.2, 'h': 0.2}

        lon, lat = get_inference_location(str(FILE.parent) + "/0.png", inference)

        self.assertAlmostEqual(lat, 53.5121564, places=4) # approximately 2m north
        self.assertAlmostEqual(lon, -113.5491390, places=4)

if __name__ == '__main__':
    unittest.main()