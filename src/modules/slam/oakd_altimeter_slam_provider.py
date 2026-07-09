import math

import numpy as np

from src.modules.autopilot.altimeter import Altimeter
from src.modules.imaging.camera import OakdCamera
from src.modules.imaging.location import LocationProvider
from src.modules.slam.slam_provider import SLAMFrame, SLAMPose, SLAMProvider


def _rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    """
    ZYX Euler rotation matrix (aerospace convention).
    Rotates a vector from body/camera frame into world frame.
    roll, pitch, yaw in radians.
    """
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)

    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])

    return Rz @ Ry @ Rx


class OakdAltimeterSLAMProvider(SLAMProvider):
    """
    Fuses OAK-D depth camera + XM125 altimeter to produce a georeferenced
    3D point cloud and drone pose.

    Coordinate convention for output points:
      X = right (camera X), Y = forward (camera Z), Z = up (altitude-anchored).
    Each call to get_frame() blocks until a fresh depth frame is available.
    """

    def __init__(
        self,
        oakd: OakdCamera,
        altimeter: Altimeter,
        location_provider: LocationProvider,
    ):
        self._oakd = oakd
        self._altimeter = altimeter
        self._location = location_provider

    def get_frame(self) -> SLAMFrame:
        # --- 1. Raw depth frame from OAK-D ---
        depth = self._oakd.capture_with_depth()

        # point_cloud shape (N, 3), units mm, OAK-D camera frame (X right, Y down, Z forward)
        pts_cam = depth.point_cloud.astype(np.float64) / 1000.0  # → metres

        # --- 2. Strip invalid points (zero or NaN) ---
        valid = ~np.any(np.isnan(pts_cam), axis=1) & ~np.all(pts_cam == 0, axis=1)
        pts_cam = pts_cam[valid]

        # --- 3. Altitude from XM125 (mm → m) ---
        alt_mm = self._altimeter.get_distance_mm()
        altitude = (alt_mm / 1000.0) if alt_mm is not None else 0.0

        # --- 4. Drone orientation from MAVLink ---
        orientation = self._location.orientation()
        roll = math.radians(orientation.roll)
        pitch = math.radians(orientation.pitch)
        yaw = math.radians(orientation.yaw)

        # --- 5. Rotate points from camera frame to world frame ---
        # OAK-D has Y pointing down; flip Y→-Y so Z is up before rotating
        pts_cam[:, 1] *= -1

        R = _rotation_matrix(roll, pitch, yaw)
        pts_world = (R @ pts_cam.T).T

        # Shift Z so the drone sits at its altimeter-measured height
        pts_world[:, 2] += altitude

        # --- 6. Build pose ---
        location = self._location.location()
        pose = SLAMPose(
            x=float(location.lat),
            y=float(location.lng),
            z=altitude,
            roll=orientation.roll,
            pitch=orientation.pitch,
            yaw=orientation.yaw,
        )

        return SLAMFrame(points=pts_world, pose=pose)
