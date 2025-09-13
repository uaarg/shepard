from typing import Callable, Literal
from src.modules.mavctl.mavctl.messages import Navigator
from src.modules.imaging.analysis import AnalysisDelegate 

def do_precision_landing(master: Navigator,
                         analysis_subscriber: Callable,
                         mode: Literal["REQUIRED", "OPPORTUNISTIC"]) -> None:
    """
    This function sets the drone into precision landing mode.

    Parameters:
        analysis_subscriber: A function that accepts a callback function which updates
                             the landing target coordinates

        mode (str): Either "REQUIRED" or "OPPORTUNISTIC".

            REQUIRED:
                The vehicle searches for a target if none is visible when
                landing is initiated, and performs precision landing if found.

            OPPORTUNISTIC:
                The vehicle uses precision landing only if the target is visible
                at landing initiation; otherwise it performs a normal landing.
    """
    def callback(coords):
        altitude = master.get_altitude().terrain # Gets the altitude above the terrain (as seen by an altimeter)
        target = Navigator.LandingTarget(x=coords[0], y=coords[1], z=altitude)
        master.broadcast_landing_target(target)

    analysis_subscriber(callback)

    if mode == "OPPORTUNISTIC":
        master.land(land_mode=1)
    elif mode == "REQUIRED":
        master.land(land_mode=2)
