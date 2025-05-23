
import time

from pymavlink import mavutil

from src.modules.autopilot.navigator import Navigator
from src.modules import imaging
import math


class Lander:
    """
A class to handle everything regarding landing that is not already handled by ardupilot
    """

    HORIZONTAL_ANGLE = math.radians(30)
    VERTICAL_ANGLE = math.radians(24)

    def __init__(self, nav, max_velocity, geofence):
        self.__spiral_route = []  # Private attribute
        self.__bounding_box_pos = []
        self.__buffer = [[],
                         []]
#        self.landing_spot = landing_spot
        self.nav = nav
        self.i = 10
        self.max_velocity = max_velocity
        self.bounding_box_detected = False
        self.bounding_box_pos = []
        self.bounding_box_log = []
        self.bounding_box_log_og = []
        self.leave_frame = False
        self.geofence = geofence
        
            
        self.null_radius = 10 # Radius in METERS of bounding box detection being ignored

    @property
    def route(self):
        return self.__spiral_route

    def generateSpiralSearch(self, numberOfLoops=10):
        """
        Generate a landing route in a square spiral pattern. The generated route is to be multiplied by the current height in metres
        to get the relative distance traveled in metres.

        :param numberOfLoops: The number of loops to be made, with a default value of 10
        :return: None
        """

        self.__spiral_route = []  # Clear the existing route
        self.y, self.x = 0, 0

        verticalScanRatio = math.tan(Lander.VERTICAL_ANGLE)
        horizontalScanRatio = math.tan(Lander.HORIZONTAL_ANGLE)
        
        step_size = 5

        steps_per_side = 2
        curr_side_iter = 0
        loops_completed = 0
        
        axis = "x"
        
        dir_x = 1
        dir_y = 1
        
        x, y = 0, 0
        
        while loops_completed != numberOfLoops:
            if axis == "x":
                x += dir_x * step_size
                for i in range(steps_per_side):
                    if len(self.__spiral_route) > 0:
                        last_x = self.__spiral_route[-1][0]
                        last_y = self.__spiral_route[-1][1]
                    else:
                        last_x = 0
                        last_y = 0

                    self.__spiral_route.append((x + last_x, y + last_y))

                axis = "y"
                dir_x *= -1
            elif axis == "y":
                y += dir_y * step_size

                for i in range(steps_per_side):
                    if len(self.__spiral_route) > 0:
                        last_x = self.__spiral_route[-1][0]
                        last_y = self.__spiral_route[-1][1]
                    else:
                        last_x = 0
                        last_y = 0

                    self.__spiral_route.append((x + last_x, y + last_y))

                axis = "x"
                dir_y *= -1
                
            curr_side_iter += 1
            
            if curr_side_iter % 2 == 0:
                steps_per_side += 1
            
            if curr_side_iter % 5 == 0:
                loops_completed += 1
        
            self.x = x
            self.y = y
            x = 0
            y = 0

    '''def executeSearch(self, altitude):
        """
        Move the drone to the next position in the landing route.

        :param Navigator: An instance of the Navigator class.
        :param route: A list of 2 elements representing the relative distance ratio to be specified as [north, east].
        :param altitude: The altitude in metres.
        :return: None
        """
        
        type_mask = self.nav.generate_typemask([0, 1])
        i = 0 
        while i <= len(self.__spiral_route) - 1:
            
            current_local_pos = self.nav.get_local_position_ned()
            print(self.geofence_check((self.__spiral_route[i][0], self.__spiral_route[i][1])))
            print(self.__spiral_route[i])
            if self.bounding_box_detected:
                print(self.bounding_box_pos)
                new_x, new_y = self.bounding_box_pos[0], self.bounding_box_pos[1]
                if len(self.bounding_box_log) == 0:
                    self.bounding_box_log.append((new_x, new_y))
                print(self.bounding_box_log)
                for bounding_box in self.bounding_box_log:
                    delta_x = bounding_box[0] - new_x - current_local_pos[0]
                    delta_y = bounding_box[1] - new_y - current_local_pos[1]
                    
                    if math.sqrt((delta_x ** 2) + (delta_y ** 2)) >= self.null_radius:
                        self.boundingBoxAction()
                        time.sleep(1/(self.max_velocity))
                        break
                self.bounding_box_detected = False
            else:
                
                if self.geofence_check((self.__spiral_route[i][0], self.__spiral_route[i][1])):

                    self.nav.set_position_target_local_ned(x = self.__spiral_route[i][0],
                                                        y = self.__spiral_route[i][1],
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
                
                    i += 1
                    time.sleep(1/(self.max_velocity))
                        
        return self.bounding_box_log

        #self.nav.set_position_relative(route[0], route[1])
'''
# Find the reason why double detection with one having high errors 
# Make task 1 script ready for comp
# Make spiral take pictures as it goes around the IR emitter to revise accuracy
# Fix heading so that the camera can face towards the inside of the spiral
# Make it so that it is plug and play for this morning

    def executeSearch(self, altitude):
        '''
        (location.north, location.east, location.down)
        to always face inwards, always face the origin
        '''
        type_mask = self.nav.generate_typemask([0, 1])
        i = 0
        origin = self.nav.get_local_position_ned()
        try:
            while i <= len(self.__spiral_route) - 1:
                current_local_pos = self.nav.get_local_position_ned()
                if self.bounding_box_detected:
                    print(self.bounding_box_pos)
                    new_x, new_y = self.bounding_box_pos[0], self.bounding_box_pos[1]
                    if len(self.bounding_box_log) == 0:
                        self.bounding_box_log.append((new_x, new_y))
                        self.bounding_box_log_og.append((new_x + current_local_pos[0], new_y + current_local_pos[1]))
                    print(self.bounding_box_log)
                    for bounding_box in self.bounding_box_log:
                        delta_x = bounding_box[0] - new_x - current_local_pos[0]
                        delta_y = bounding_box[1] - new_y - current_local_pos[1]

                        if math.sqrt((delta_x ** 2) + (delta_y ** 2)) >= self.null_radius:
                            self.boundingBoxAction()
                            time.sleep(2/(self.max_velocity))
                            break
                    self.bounding_box_detected = False
                else:

                    # NOTE: THESE ARE ABSOLUTE COORDINATES
                    # Spiral search is in absolute coordinates in which it adds the offset to the origin
                    self.nav.set_position_target_local_ned(x = self.__spiral_route[i][0] + origin[0] - (self.__spiral_route[4][0] / 2),
                                                        y = self.__spiral_route[i][1] + origin[1] - (self.__spiral_route[9][1] / 2),
                                                        z = -altitude,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_NED)

                    i += 1
                   
                     
                                  # Increase if the drone is overriding itself or moving too quickly
                    # Decrease if there is more "stop, start" than desirable
                    time.sleep(1.5/(self.max_velocity))

            print(self.bounding_box_log_og)
        finally:
            return self.bounding_box_log_og


    def boundingBoxAction(self):
        # go to bounding box and go around it in a square
        type_mask = self.nav.generate_typemask([0, 1]) 
        
        current_local_pos = self.nav.get_local_position_ned()
        time.sleep(1)
        
        x, y = self.bounding_box_pos[0], self.bounding_box_pos[1]
        if self.geofence_check((x + 2, y)) and self.geofence_check((x, y + 2)) and self.geofence_check((x + 2, y + 2)):
            self.nav.set_position_target_local_ned(x = x,
                                                        y = y,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
            time.sleep((math.sqrt(x ** 2 + y ** 2)/(self.max_velocity)))
            self.nav.set_position_target_local_ned(x = 2,
                                                        y = 0,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
            time.sleep((3/(self.max_velocity)))
            self.nav.set_position_target_local_ned(x = 0,
                                                        y = 2,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
            time.sleep(3/(self.max_velocity))
            self.nav.set_position_target_local_ned(x = -2,
                                                        y = 0,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
            time.sleep((3/(self.max_velocity)))
            self.nav.set_position_target_local_ned(x = 0,
                                                        y = -2,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
            time.sleep((3/(self.max_velocity)))
            
            self.nav.set_position_target_local_ned(x = -x,
                                                        y = -y,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
            time.sleep((math.sqrt(x ** 2 + y ** 2)/(self.max_velocity)))

        else:
            self.nav.set_position_target_local_ned(x = x,
                                                        y = y,
                                                        type_mask=type_mask, 
                                                        coordinate_frame = mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED)
            time.sleep((math.sqrt(x ** 2 + y ** 2)/(self.max_velocity)))
 

        self.bounding_box_detected = False
        self.bounding_box_log.append((x, y))
        self.bounding_box_log_og.append((x + current_local_pos[0], y + current_local_pos[1]))

    def detectBoundingBox(self, _, bounding_box_pos):
        if bounding_box_pos:
            if not self.leave_frame:
                self.bounding_box_detected = True
                self.bounding_box_pos = bounding_box_pos
        else:

            if self.leave_frame:
                self.leave_frame = False

    def geofence_check(self, point):
        # Adapted from code provided by Aiden
        #lat, lon, alt = self.nav.get_global_position()
        lat, lon = point[1], point[0]
        hitcount = 0
        for i in range(len(self.geofence) - 1):
            # Model geofence lines as y = mx + b
            A = self.geofence[i]
            B = self.geofence[i + 1]

            m = (B[1] - A[1]) / (B[0] - A[0])

            # Handling the case of delta_lon == 0
            if abs(m) == float('inf'):
                m = (B[1] - A[1])/ (B[0] - A[0] + 0.00000001)

            b = A[0] - m * A[0]

            x = (lat - b) / m

            if x > lon and lat > min(A[1], B[1]) and lat < max(A[1], B[1]):
                hitcount += 1
        return bool(hitcount & 1)



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
'''
                if i == 0:
                    self.nav.set_heading(0)
                    time.sleep(5)
                elif ((i - 1) % 5 == 0) and i != 1:
                    self.nav.set_heading_relative(90)
                else:
                    self.nav.set_heading_relative(0)
                
'''             



if __name__ == "__main__":
    main()
