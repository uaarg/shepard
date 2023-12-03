import math
import time
from Navigator import Navigator

class LandingSpotFinder:

    HORIZONTAL_ANGLE = math.radians(30)
    VERTICAL_ANGLE = math.radians(24)
    

    def __init__(self):
        self.__route = []  # Private attribute

    @property
    def route(self):
        return self.__route

    def generateRoute(self, numberOfLoops=10):
        self.__route = []  # Clear the existing route
        self.y, self.x = 0, 0

        verticalScanRatio = math.tan(LandingSpotFinder.VERTICAL_ANGLE)
        horizontalScanRatio = math.tan(LandingSpotFinder.HORIZONTAL_ANGLE)

        for i in range(2, numberOfLoops, 2):
            for j in range(4):
                if j == 0:
                    self.y = self.y - verticalScanRatio
                    self.__route.append([self.y, self.x])
                    for k in range(i - 1):
                        self.x = self.x + horizontalScanRatio
                        self.__route.append([self.y, self.x])
                if j == 1:
                    for k in range(i):
                        self.y = self.y + verticalScanRatio
                        self.__route.append([self.y, self.x])
                if j == 2:
                    for k in range(i):
                        self.x = self.x - horizontalScanRatio
                        self.__route.append([self.y, self.x])
                if j == 3:
                    for k in range(i):
                        self.y = self.y - verticalScanRatio
                        self.__route.append([self.y, self.x])
                        
    def goNext(self,Navigator,route):
        
        altitude= Navigator.vehicle.location.global_relative_frame.alt
        
        Navigator.set_heading(0) # to make sure drone is facing 
        Navigator.set_position_relative(route[0] * altitude, route[1] * altitude)
        
def main():
        
        LandingSpotFinder1 = LandingSpotFinder()
        Navigator1 = Navigator()
        
        LandingSpotFinder1.generateRoute()  # Call the method to generate the route
        
        for i in LandingSpotFinder1.route:
            #add code to break the loop when landing spot is found
            LandingSpotFinder1.goNext(Navigator1,i)
            time.sleep(5)

    

if __name__ == "__main__":
    main()
    