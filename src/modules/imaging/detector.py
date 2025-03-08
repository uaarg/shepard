import cv2
import numpy as np
import logging
import os
import glob

class Detector:
    """
    Detects red balloons in a given image and returns the direction and distance
    to the nearest balloon from the center of the image. The direction is one of
    the following: left, right, up, down, or center. The distance is a normalized
    value between 0 and 1.
    """

    def __init__(self, image_path=None):
        self.image_path = image_path

    def detect_red_balloons(self, image_path): 
        """
        Main logic

        Returns:
            direction (str): One of left, right, up, down, or center.
            distance (float): Normalized distance from the center of the image to the
                nearest balloon, between 0 and 1.
            detected (bool): Whether a red balloon was detected.
        """
        self.image_path = image_path
        logging.info(f"Detecting red balloons... {self.image_path}")
        if self.image_path is None:
            logging.error("No image provided")
            return "none", 0, 
            
        img = cv2.imread(self.image_path)
        if img is None:
            logging.error(f"Image not found: {image_path}")
            return "none", 0, False
        
        # Get dimensions and center of the image
        height, width = img.shape[:2]
        center_x, center_y = width // 2, height // 2
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define improved range for red color detection
        # Two ranges needed because red wraps around the hue spectrum in HSV
        lower_red1 = np.array([0, 100, 100])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 100, 100])
        upper_red2 = np.array([180, 255, 255])
        
        # Create masks for red detection
        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)
        
        # Apply morphological operations to remove noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # No contours means no red balloons
        if not contours:
            return "none", 0, False
        
        # Filter out small contours that might be noise
        min_contour_area = 100  # Adjust as needed
        valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
        
        if not valid_contours:
            return "none", 0, False
        
        # For multiple balloons, we want to find the one closest to the center
        # Find the centroid of all balloons and find the closest one
        all_balloon_points = np.vstack([cnt for cnt in valid_contours])
        M = cv2.moments(all_balloon_points)
        
        if M["m00"] == 0:
            return "none", 0, False
        
        # Calculate the centroid of all red regions
        balloon_center_x = int(M["m10"] / M["m00"])
        balloon_center_y = int(M["m01"] / M["m00"])
        
        # Calculate vector from image center to balloon center
        dx = balloon_center_x - center_x
        dy = balloon_center_y - center_y
        
        # Normalize distance to be between 0 and 1
        # Maximum possible distance is from center to corner
        max_distance = np.sqrt((width/2)**2 + (height/2)**2)
        distance = np.sqrt(dx**2 + dy**2) / max_distance
        
        # Determine direction - only one primary direction as specified
        if distance < 0.1:  # If balloons are close to center
            direction = "center"
        elif abs(dx) > abs(dy):
            direction = "right" if dx > 0 else "left"
        else:
            direction = "down" if dy > 0 else "up"
        
        return direction, distance, True

    def process_image_directory(self, directory_path, pattern=".png"): #do not add "/" at the end of directory path
        """
        Process a directory of images by detecting red balloons and printing the results.

        Parameters
        ++++++++++
        directory_path : str
            Path to the directory of images to process
        pattern : str, optional
            Pattern for selecting images in the directory, default is "*.jpg"

        Notes
        +++++
        The function will print the results of balloon detection for each image in the
        directory. If no balloons are detected in an image, it will print "No red balloons
        detected". Otherwise, it will print the direction and normalized distance from the
        center of the image to the nearest balloon.
        """
        for file in os.listdir(directory_path):
            if ".png" in file:
                image_path = directory_path + "/" + file
            else:
                print(f"picture not taken yet")
                return None 
            
        print(image_path)
        
        # Process each image in the directory
        print(f"Processing image: {image_path}...")
        direction, distance, detected = self.detect_red_balloons(image_path=image_path)
        
        if detected:
            print(f"Red balloon detected: Move {direction}, Distance: {distance:.2f}")
            return direction, distance
        else:
            print("No red balloons detected")
            return None

if __name__ == "__main__":
    # Process a single image
    image_path = "path/to/image.jpg"
    detector = Detector(image_path=image_path)
    if os.path.exists(image_path):
        direction, distance, detected = detector.detect_red_balloons(image_path=image_path)
        
        if detected:
            print(f"Red balloon(s) detected: Move {direction}, Distance: {distance:.2f}")
        else:
            print("No red balloons detected")
    
