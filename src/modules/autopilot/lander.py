import math
import time

from pymavlink import mavutil

from src.modules.autopilot.navigator import Navigator
from src.modules import imaging

class Lander:
    """
    A class to handle everything regarding landing that is not already handled by ardupilot
    """

    HORIZONTAL_ANGLE = math.radians(30)
    VERTICAL_ANGLE = math.radians(24)

    def __init__(self, nav, landing_spot=(0, 0)):
        self.__route = []  # Private attribute
        self.__buffer = [[],
                         []]
        self.landing_spot = landing_spot
        self.nav = nav
        self.i = 10
        


    @property
    def route(self):
        return self.__route

    def generateRoute(self, numberOfLoops=10):
        """
        Generate a landing route in a square spiral pattern. The generated route is to be multiplied by the current height in metres
        to get the relative distance traveled in metres.

        :param numberOfLoops: The number of loops to be made, with a default value of 10
        :return: None
        """

        self.__route = []  # Clear the existing route
        self.y, self.x = 0, 0

        verticalScanRatio = math.tan(Lander.VERTICAL_ANGLE)
        horizontalScanRatio = math.tan(Lander.HORIZONTAL_ANGLE)

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

    def goNext(self, Navigator, route, altitude):
        """
        Move the drone to the next position in the landing route.

        :param Navigator: An instance of the Navigator class.
        :param route: A list of 2 elements representing the relative distance ratio to be specified as [north, east].
        :param altitude: The altitude in metres.
        :return: None
        """

        type_mask = Navigator.generate_typemask([0, 1, 2])

        Navigator.set_position_target_local_ned(x = route[0] * altitude,
                                                y = route[1] * altitude,
                                                z = -altitude,
                                                type_mask=type_mask, 
                                                mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)

    def enable_precision_land(self, Navigator):

        # NOTE: CHANGE THE CAMERA TYPE DURING ACTUAL USE
        camera = imaging.camera.DebugCamera("./res/test-image.jpeg")
        
        analysis = imaging.analysis.ImageAnalysisDetector(camera = camera, nav = Navigator)

        analysis.subscribe(self._precision_land)
        analysis.run()

    def _precision_land(self, im, lon, lat, x, y):

        # Append new values for position to the buffer and compute the moving average, taking the new values into account. 
        # Adjust buffer size depending on the refresh rate of the imaging script

        buffer_size = 5

        self.__buffer[0].append(x)
        self.__buffer[1].append(y)

        x = sum(self.__buffer[0]) / len(self._buffer[0])
        y = sum(self.__buffer[1] / len(self.__buffer[1]))
        

        if len(self.__buffer[0]) >= buffer_size and len(self.__buffer[1]) >= buffer_size:
            type_mask = self.nav.generate_typemask([0, 1, 2])

            
            self.nav.set_postion_target_local_NED(x = self.__buffer[0][-1], y = self.__buffer[1][-1], z = -(self.i), type_mask = type_mask)

            self.i -= 1

            # Maintain the size of the buffer
            self.__buffer[0].pop(0)
            self.__buffer[1].pop(0)



def main():
    LandingSpotFinder1 = Lander()
    Navigator1 = Navigator()

    LandingSpotFinder1.generateRoute()  # Call the method to generate the route

    for i in LandingSpotFinder1.route:
        # add code to break the loop when landing spot is found
        LandingSpotFinder1.goNext(Navigator1, i)
        time.sleep(5)


if __name__ == "__main__":
    main()
