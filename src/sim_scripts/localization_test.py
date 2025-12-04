from src.modules.imaging import util
import numpy as np

closeSphereXYZ = np.array([0, 0, 0]).reshape(-1, 1)
farSphereXYZ = np.array([0, 1, 0]).reshape(-1, 1)

pixelCoordsClose = np.array([327, 202]).reshape(-1, 1)
pixelCoordsFar = np.array([328, 162]).reshape(-1, 1)

x = np.hstack([pixelCoordsClose, pixelCoordsFar])
X = np.hstack([closeSphereXYZ, farSphereXYZ])

# Calibrate Camera
P = util.dlt(x, X)
print(P)

