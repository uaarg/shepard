# Tests can be run with ./scripts/test.sh
# They will run all files in the test/ directory starting with 'test_'.
# Then, all functions starting with 'test_' will be run in that file. If the
# function raises an error, the test fails. Otherwise, the test passes.
# See test/test_camera.py for an example.

from src.modules.imaging.location import DebugLocationProvider


def test_get_location():
    # TODO
    raise NotImplementedError()


def test_get_heading():
    # TODO
    raise NotImplementedError()


def test_get_altitude():
    # TODO
    raise NotImplementedError()


def test_get_orientation():
    # TODO
    raise NotImplementedError()


def test_position_changes():
    initial_location = None  # TODO
    loc = DebugLocationProvider(initial_location)

    # ... assert location

    new_location = None  # TODO
    loc.debug_change_location(new_location)

    # ... assert new location
