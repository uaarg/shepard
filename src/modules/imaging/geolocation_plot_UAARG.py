import math
import matplotlib.pyplot as plt

# Function to calculate distance between two latitude/longitude points
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance in meters between two points
    on the Earth's surface specified in decimal degrees.
    """
    EARTH_RADIUS = 6371000  # Earth radius in meters
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Differences in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = EARTH_RADIUS * c
    return distance

# Read and parse the file
data = []
with open("/Users/phillipjuricek/Desktop/UAARG/shepard/october_19.txt", "r") as file:
    for line in file:
        line = line.strip()
        if "," in line:  # Ensure the line contains comma-separated values
            try:
                # Split the line into latitude and longitude
                parts = line.split(",")
                lat = float(parts[0].strip())  # Latitude
                lon = float(parts[1].strip())  # Longitude
                data.append((lat, lon))
            except ValueError:
                pass  # Ignore lines that don't parse correctly

# Calculate distances between consecutive points
distances = []
for i in range(len(data) - 1):
    lat1, lon1 = data[i]
    lat2, lon2 = data[i + 1]
    distance = haversine(lat1, lon1, lat2, lon2)
    distances.append(distance)

# Debug: Print distances (optional)
print("Distances between points (in meters):", distances)

# Convert lat/lon to relative distances in meters for plotting
relative_positions = []
base_lat, base_lon = data[0]  # Use the first point as the origin
for lat, lon in data:
    x = haversine(base_lat, base_lon, base_lat, lon)  # East-West distance
    y = haversine(base_lat, base_lon, lat, base_lon)  # North-South distance
    relative_positions.append((x, y))

# Separate x and y coordinates for plotting
x_coords = [pos[0] for pos in relative_positions]
y_coords = [pos[1] for pos in relative_positions]

# Create the line plot
plt.plot(x_coords, y_coords, marker='o')

# Add labels and title
plt.xlabel("East-West Distance (meters)")  # X-axis title
plt.ylabel("North-South Distance (meters)")  # Y-axis title
plt.title("october_19.txt geolocation data in metres")
plt.grid()

# Show the plot
plt.show()
