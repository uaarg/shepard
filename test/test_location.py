# Tests can be run with ./scripts/test.sh
# They will run all files in the test/ directory starting with 'test_'.
# Then, all functions starting with 'test_' will be run in that file. If the
# function raises an error, the test fails. Otherwise, the test passes.
# See test/test_camera.py for an example.

from src.modules.imaging.location import DebugLocationProvider, LatLng, Heading, Rotation


def test_get_location():
    loc = DebugLocationProvider()
    loc.debug_change_location(lat=10.0, lng=20.0)

    assert loc.location() == LatLng(10.0, 20.0), "Location did not match expected value"

def test_get_heading():
    loc = DebugLocationProvider()
    loc.debug_change_location(heading=45.0)

    assert loc.heading() == Heading(45.0), "Heading did not match expected value"


def test_get_altitude():
    loc = DebugLocationProvider()
    loc.debug_change_location(altitude=100.0)

    assert loc.altitude() == 100.0, "Altitude did not match expected value"



def test_get_orientation():
    loc = DebugLocationProvider()
    loc.debug_change_location(pitch=10.0, roll=20.0, yaw=30.0)

    assert loc.orientation() == Rotation(10.0, 20.0, 30.0), "Orientation did not match expected value"



def test_position_changes():
    loc = DebugLocationProvider()

    # Initial change
    loc.debug_change_location(lat=10.0, lng=20.0)
    assert loc.location() == LatLng(10.0, 20.0), "Initial location did not match expected value"

    # Change to new location
    loc.debug_change_location(lat=40.0, lng=50.0)
    assert loc.location() == LatLng(40.0, 50.0), "New location did not match expected value"
