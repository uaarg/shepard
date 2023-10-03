import dronekit_sitl


class Simulator:
    """
    A class to create and handle a simulated drone.
    """

    __sitl = None
    __conn_str = None
    __gcs_conn_str = None

    @property
    def sitl(self):
        return self.__sitl

    @property
    def conn_str(self):
        return self.__conn_str

    @property
    def gcs_conn_str(self):
        return self.__gcs_conn_str

    def __init__(self):
        self.__sitl = dronekit_sitl.start_default()
        self.__conn_str = self.__sitl.connection_string()
        # TODO: Find a way to set gcs_conn_str programmatically
        self.__gcs_conn_str = "127.0.0.1:5763"

    def __del__(self):
        self.__sitl.stop()
