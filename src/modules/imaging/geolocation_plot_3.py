import pyproj
import matplotlib.pyplot as plt

# Example data: Latitude and Longitude in degrees
latitudes = [49.2827, 49.2829, 49.2831]
longitudes = [-123.1207, -123.1208, -123.1209]

# Initialize a UTM projection
# You can replace 'EPSG:4326' (WGS84) with your specific CRS if needed
wgs84 = pyproj.CRS("EPSG:4326")  # WGS 84 Latitude and Longitude
utm_zone = pyproj.CRS("EPSG:32610")  # Example: UTM zone 10N, replace with your zone

# Create a transformer
transformer = pyproj.Transformer.from_crs(wgs84, utm_zone, always_xy=True)

# Convert lat/lon to UTM
utm_coords = [transformer.transform(lon, lat) for lon, lat in zip(longitudes, latitudes)]

# Use the first point as the origin
origin_x, origin_y = utm_coords[0]
relative_coords = [(x - origin_x, y - origin_y) for x, y in utm_coords]

# Separate X and Y for plotting
x_coords, y_coords = zip(*relative_coords)

# Plot the data
plt.figure(figsize=(8, 6))
plt.scatter(x_coords, y_coords, color='blue', label='Data Points')
plt.xlabel('Relative UTM Easting (m)')
plt.ylabel('Relative UTM Northing (m)')
plt.title('Data Points Relative to Origin (First Point)')
plt.axhline(0, color='black', linewidth=0.8, linestyle='--')
plt.axvline(0, color='black', linewidth=0.8, linestyle='--')
plt.legend()
plt.grid(True)
plt.show()
