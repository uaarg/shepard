import csv
from typing import List, Tuple
from geopy.distance import distance
from numpy import array, mean


class Command:
    """
    A class that contains all the information contained in a typical MavLink command
    """

    def __init__(self, frame: int = 0, command_id: int = 16,
                 param1: float = 0, param2: float = 0, param3: float = 0, param4: float = 0,
                 latitude: float = 0, longitude: float = 0, altitude: float = 0, name: str = None):
        self.frame = frame
        self.command_id = command_id
        self.param1 = param1
        self.param2 = param2
        self.param3 = param3
        self.param4 = param4
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.attributes = (self.frame, self.command_id, self.param1, self.param2, self.param3, self.param4,
                           self.latitude, self.longitude, self.altitude)
        self.xy = (self.latitude, self.longitude)
        self.xyz = (self.latitude, self.longitude, self.altitude)
        self.name = name

    def to_mission_planner(self, sequence: int, is_home: bool = False):
        """
        Output a string that can be added to the Mission Planner waypoint file

        :param sequence: Waypoint # in the mission
        :param is_home: A boolean value that determines whether this is a home location
        :return: a string that can be added to the Mission Planner waypoint file
        """

        return '\t'.join((str(sequence), str(int(is_home)), *map(str, self.attributes), '1'))

    def to_dronekit(self, target_system: int = 0, target_component: int = 0, sequence: int = 0,
                    current: int = 0, autocontinue: int = 0):
        """
        Convert the command to the dronekit Command format

        :param target_system: This can be set to any value (DroneKit changes the value to the MAVLink ID of the
        connected vehicle before the command is sent).
        :param target_component: The component id if the message is intended for a particular component within the
        target system (for example, the camera). Set to zero (broadcast) in most cases.
        :param sequence: The sequence number within the mission (the autopilot will reject messages sent out of sequence
        ). This should be set to zero as the API will automatically set the correct value when uploading a mission.
        :param current: Set to zero (not supported).
        :param autocontinue: Set to zero (not supported).
        :return: A tuple with elements that can be passed to the dronekit Command class to create MavLink commands
        """

        return (target_system, target_component, sequence) + \
            self.attributes[:2] + (current, autocontinue) + self.attributes[2:]


class Mission:
    """
    A series of commands that make up a mission
    """

    def __init__(self, commands: List[Command] = None):
        self.commands = commands if commands else []
        self.xy = list(command.xy for command in self.commands)
        self.xyz = list(command.xyz for command in self.commands)
        self.attributes = list(command.attributes for command in self.commands)

    def __len__(self):
        return len(self.commands)

    def add(self, command: Command):
        """
        Add new command to the mission

        :param command: A Command instance that contains the relevant information
        :return: A list of commands instances
        """

        self.commands.append(command)
        pass

    def save(self, file_name: str = 'waypoints', file_type: str = '.waypoints'):
        """
        Save the mission to a file, exact type and format varies

        :param file_name: Name of the file
        :param file_type: Filetype of the file, Mission Planner is .waypoints
        :return: A file that contains the mission's information
        """

        mission_file = open(file_name + file_type, 'w')
        if file_type == '.waypoints':
            mission_file.write('QGC WPL 110\n')  # Meaning unclear as for now, needed for Mission Planner waypoints file
            for sequence, command in enumerate(self.commands):
                is_home = False if sequence != 0 else True
                line = command.to_mission_planner(sequence, is_home) + '\n'
                mission_file.write(line)
            mission_file.close()
            pass

    def to_dronekit(self):
        """
        Convert the Mission to a series of dronekit Command format

        :return: A List of dronekit-formatted commands, each command is a list with elements that can be passed to the
        dronekit Command Class to create MavLink commands
        """
        if self.commands:
            commands = []
            for command in self.commands:
                commands.append(command.to_dronekit())
            return commands

    @classmethod
    def load_from_wkt(cls, file_name: str, encoding: str = 'UTF-8'):
        """
        Load a .csv file that uses WKT format to represent AEAC waypoints, this .csv file is created by first loading
        the waypoints table in Excel from the AEAC rulebook, then saving it as a csv file

        :param file_name: Path to the file
        :param encoding: Name of the encoding to decode the file
        :return: A Mission instance that contains all the waypoints in the .csv file
        """

        waypoints = []
        with open(file_name, encoding=encoding) as wkt_file:
            wkt_reader = csv.reader(wkt_file)
            next(wkt_reader, None)  # Skip header
            for row in wkt_reader:
                point = list(map(float, row[0][7:-1].split()))
                point.reverse()  # Latitude and longitude is inverted in the AEAC rulebook because apparently the
                # Aerial Evolutionary Association of Canada doesn't know how to list GPS coordinates
                name = row[1]
                waypoints.append(Command(0, 16, 0, 0, 0, 0, *point, 0, name=name))
            return Mission(waypoints)

    @classmethod
    def load_from_waypoint(cls, file_name, encoding: str = 'UTF-8'):
        """
        Load a .waypoint file saved by Mission Planner that contains information about mission and fences

        :param file_name: Path to the file
        :param encoding: Name of the encoding to decode the file
        :return:A mission instance that contains all the waypoints in the .waypoint file
        """

        waypoints = []
        with open(file_name, encoding=encoding) as waypoint_file:
            waypoint_reader = csv.reader(waypoint_file, delimiter='\t')
            next(waypoint_reader, None)  # Skip the first line of .waypoint file
            for row in waypoint_reader:
                command = list(map(float, row[2:10]))
                waypoints.append(Command(*command))
            return Mission(waypoints)


def gps_to_cartesian(gps_coordinates: List[Tuple[float, float]], origin: Tuple[float, float] = None):
    """
    Convert a series of GPS coordinates to cartesian coordinates

    :param gps_coordinates: A list of GPS coordinates to be converted
    :param origin: gps coordinate of the origin in the cartesian coordinate system
    :return: A list of cartesian coordinates that represent the GPS coordinates
    """

    gps_coordinates = array(gps_coordinates)
    if origin is None:
        origin = mean(gps_coordinates, axis=0)
    else:
        origin = array(origin)
    xy = []
    for coordinate in gps_coordinates:
        x = distance(origin, (origin[0], coordinate[1])).m
        y = distance(origin, (coordinate[0], origin[1])).m
        x = -x if coordinate[1] < origin[1] else x
        y = -y if coordinate[0] < origin[0] else y
        xy.append((x, y))
    return xy


if __name__ == '__main__':
    test = 3
    if test == 1:  # Test loading from wkt and save to .waypoints
        test_mission = Mission.load_from_wkt('test_waypoints/2023_AEAC_Task_Waypoints.csv')
        test_mission.save()

    elif test == 2:  # Test loading from wkt and convert to dronekit command format
        test_mission = Mission.load_from_wkt('test_waypoints/2023_AEAC_Task_Waypoints.csv')
        mission_matrix = test_mission.to_dronekit()
        print(mission_matrix)

    elif test == 3:  # Test converting from gps to cartesian
        import matplotlib.pyplot as plt
        test_fence = Mission.load_from_waypoint('test_waypoints/mission_planner_example_fence.waypoints')
        test_gps_coordinates = test_fence.xy[1:]
        result_cartesian = gps_to_cartesian(test_gps_coordinates)
        draw_cartesian = result_cartesian + [result_cartesian[0]]
        plt.plot(*list(zip(*draw_cartesian)))
        plt.show()
