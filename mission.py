import csv
from typing import List


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
    def load_from_wkt(cls, file_name: str):
        """
        Load a .csv file that uses WKT format to represent AEAC waypoints, this .csv file is created by first loading
        the waypoints table in Excel from the AEAC rulebook, then saving it as a csv file

        :param file_name: Path to the file
        :return: A Mission instance that contains all the waypoints in the .csv file
        """

        waypoints = []
        with open(file_name) as wkt_file:
            wkt_reader = csv.reader(wkt_file)
            next(wkt_reader, None)
            for row in wkt_reader:
                point = list(map(float, row[0][7:-1].split()))
                point.reverse()  # Latitude and longitude is inverted in the AEAC rulebook because apparently the
                # Aerial Evolutionary Association of Canada doesn't know how to list GPS coordinates
                name = row[1]
                waypoints.append(Command(0, 16, 0, 0, 0, 0, *point, 0, name=name))
            return Mission(waypoints)


if __name__ == '__main__':
    test = 2
    if test == 1:
        test_mission = Mission.load_from_wkt('test_waypoints/2023_AEAC_Task_Waypoints.csv')
        test_mission.save()
    elif test == 2:
        test_mission = Mission.load_from_wkt('test_waypoints/2023_AEAC_Task_Waypoints.csv')
        mission_matrix = test_mission.to_dronekit()
        print(mission_matrix)
