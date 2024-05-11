import math
from src.modules.imaging.location import (DebugLocationProvider,
                                          MAVLinkLocationProvider, LatLng,
                                          Heading, Rotation)
from src.modules.imaging.mavlink import MAVLinkDelegateMock
from pymavlink.dialects.v20 import all as dialect


def test_get_location():
    loc = DebugLocationProvider()
    loc.debug_change_location(lat=10.0, lng=20.0)

    assert loc.location() == LatLng(
        10.0, 20.0), "Location did not match expected value"


def test_get_location_partial():
    loc = DebugLocationProvider()
    loc.debug_change_location(lat=10.0, lng=20.0)
    loc.debug_change_location(lat=15.0)  # Missing lng

    assert loc.location() == LatLng(
        15.0, 20.0), "Location did not match expected value"


def test_get_heading():
    loc = DebugLocationProvider()
    loc.debug_change_location(heading=45.0)

    assert loc.heading() == Heading(
        45.0), "Heading did not match expected value"


def test_get_altitude():
    loc = DebugLocationProvider()
    loc.debug_change_location(altitude=100.0)

    assert loc.altitude() == 100.0, "Altitude did not match expected value"


def test_get_orientation():
    loc = DebugLocationProvider()
    loc.debug_change_location(pitch=10.0, roll=20.0, yaw=30.0)

    assert loc.orientation() == Rotation(
        10.0, 20.0, 30.0), "Orientation did not match expected value"


def test_get_orientation_partial():
    loc = DebugLocationProvider()
    loc.debug_change_location(pitch=10.0, roll=20.0, yaw=30.0)
    loc.debug_change_location(pitch=12.0)

    assert loc.orientation() == Rotation(
        12.0, 20.0, 30.0), "Orientation did not match expected value"


def test_position_changes():
    loc = DebugLocationProvider()

    # Initial change
    loc.debug_change_location(lat=10.0, lng=20.0)
    assert loc.location() == LatLng(
        10.0, 20.0), "Initial location did not match expected value"

    # Change to new location
    loc.debug_change_location(lat=40.0, lng=50.0)
    assert loc.location() == LatLng(
        40.0, 50.0), "New location did not match expected value"


def test_get_MAVLink_location():
    mavlink = MAVLinkDelegateMock()
    loc_mavlink = MAVLinkLocationProvider(mavlink)

    # Create a mock GLOBAL_POSITION_INT message for the initial location
    initial_message = dialect.MAVLink_global_position_int_message(
        time_boot_ms=0,  # Assuming a timestamp of 0 for the test
        lat=int(10.0 * 1e7),  # Latitude in degE7
        lon=int(20.0 * 1e7),  # Longitude in degE7
        alt=1000,  # Altitude in mm above MSL
        relative_alt=500,  # Altitude in mm above the ground
        vx=0,
        vy=0,
        vz=0,  # Ground X, Y, Z Speed
        hdg=0  # Heading
    )
    mavlink.send(initial_message)
    assert loc_mavlink.location() == LatLng(
        10.0, 20.0), "Initial location did not match expected value"

    # Create a mock GLOBAL_POSITION_INT message for the new location
    new_message = dialect.MAVLink_global_position_int_message(
        time_boot_ms=0,  # Assuming a timestamp of 0 for the test
        lat=int(40.0 * 1e7),  # Latitude in degE7
        lon=int(50.0 * 1e7),  # Longitude in degE7
        alt=2000,  # Altitude in mm above MSL
        relative_alt=1000,  # Altitude in mm above the ground
        vx=0,
        vy=0,
        vz=0,  # Ground X, Y, Z Speed
        hdg=0  # Heading
    )
    mavlink.send(new_message)
    assert loc_mavlink.location() == LatLng(
        40.0, 50.0), "New location did not match expected value"


def test_get_MAVLink_heading():
    mavlink = MAVLinkDelegateMock()
    loc_mavlink = MAVLinkLocationProvider(mavlink)

    # Create a mock VFR_HUD message for heading
    heading_message = dialect.MAVLink_global_position_int_message(
        time_boot_ms=0,
        lat=0,
        lon=0,
        alt=2000,  # Altitude in mm above MSL
        relative_alt=
        0,  # Relative altitude in mm above the ground (not used in this test)
        vx=0,
        vy=0,
        vz=0,  # Ground X, Y, Z Speed (not used in this test)
        hdg=150 * 1e7  # Heading in degE7
    )
    mavlink.send(heading_message)

    # Check if the MAVLinkLocationProvider reports the heading correctly
    assert loc_mavlink.heading() == Heading(
        150), "Heading did not match expected value"


def test_get_MAVLink_altitude():
    mavlink = MAVLinkDelegateMock()
    loc_mavlink = MAVLinkLocationProvider(mavlink)

    # Create a mock GLOBAL_POSITION_INT message for altitude
    altitude_message = dialect.MAVLink_global_position_int_message(
        time_boot_ms=0,  # Timestamp for the test
        lat=0,  # Dummy latitude
        lon=0,  # Dummy longitude
        alt=15000,  # Altitude in mm above MSL
        relative_alt=0,  # Relative altitude in mm above the ground
        vx=0,
        vy=0,
        vz=0,  # Ground X, Y, Z Speed
        hdg=0  # Heading
    )
    mavlink.send(altitude_message)

    # Check if the MAVLinkLocationProvider reports the altitude correctly
    assert loc_mavlink.altitude(
    ) == 15.0, "Altitude did not match expected value in meters"


def test_get_MAVLink_orientation():
    mavlink = MAVLinkDelegateMock()
    loc_mavlink = MAVLinkLocationProvider(mavlink)

    # Create a mock ATTITUDE message for orientation
    orientation_message = dialect.MAVLink_attitude_message(
        time_boot_ms=0,  # Timestamp for the test
        pitch=0.1,  # Pitch in radians
        roll=0.2,  # Roll in radians
        yaw=0.3,  # Yaw in radians
        rollspeed=0,  # Roll speed (not used in this test)
        pitchspeed=0,  # Pitch speed (not used in this test)
        yawspeed=0  # Yaw speed (not used in this test)
    )
    mavlink.send(orientation_message)

    # Check if the MAVLinkLocationProvider reports the orientation correctly
    expected_orientation = Rotation(math.degrees(0.1), math.degrees(0.2),
                                    math.degrees(0.3))
    actual_orientation = loc_mavlink.orientation()
    assert actual_orientation == expected_orientation, "Orientation did not match expected value"


def test_get_MAVLink_position_changes():
    mavlink = MAVLinkDelegateMock()
    loc_mavlink = MAVLinkLocationProvider(mavlink)

    # Send a mock GLOBAL_POSITION_INT message for initial position
    initial_position_message = dialect.MAVLink_global_position_int_message(
        time_boot_ms=0,
        lat=int(10.0 * 1e7),
        lon=int(20.0 * 1e7),
        alt=1000,
        relative_alt=500,
        vx=0,
        vy=0,
        vz=0,
        hdg=0.0)
    mavlink.send(initial_position_message)

    # Verify initial position
    assert loc_mavlink.location() == LatLng(
        10.0, 20.0), "Initial location did not match expected value"

    # Send another mock GLOBAL_POSITION_INT message for new position
    new_position_message = dialect.MAVLink_global_position_int_message(
        time_boot_ms=1000,  # Simulate a time after the initial message
        lat=int(40.0 * 1e7),
        lon=int(50.0 * 1e7),
        alt=2000,
        relative_alt=1000,
        vx=0,
        vy=0,
        vz=0,
        hdg=45.0 * 1e7)
    mavlink.send(new_position_message)

    # Verify new position
    assert loc_mavlink.location() == LatLng(
        40.0, 50.0), "New location did not match expected value"
    assert loc_mavlink.heading() == Heading(
        45.0), "New heading did not match expected value"
    assert loc_mavlink.altitude(
    ) == 2.0, "New altitude did not match expected value in meters"


def test_get_MAVLink_position_not_init():
    mavlink = MAVLinkDelegateMock()
    loc_mavlink = MAVLinkLocationProvider(mavlink)

    def assert_raises(f):
        try:
            f()
        except ValueError:
            pass
        else:
            assert False, "Did not raise when accessing an uninitialized value"

    methods = [
        loc_mavlink.altitude,
        loc_mavlink.location,
        loc_mavlink.heading,
        loc_mavlink.orientation,
    ]
    for method in methods:
        assert_raises(method)
