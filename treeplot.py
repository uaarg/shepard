import matplotlib.pyplot as plt

import tree


# CHANGE THESE TO CHANGE PARAMETERS OF PLOT
DATA_SOURCE = "randomdata.csv"
INTERSECT_SAFE = True

# color variables
res_col = 'darkorange'
waypoint_col = 'royalblue'
start_col = 'tomato'
target_col = 'limegreen'

# get all required data
parsed_nodes = tree.parse_data(DATA_SOURCE)
waypoints, nofly_region, margin_region = tree.create_safe_waypoints(parsed_nodes)

# original nodes
points_x = [i[0] for i in parsed_nodes.values() if i[2] == 'obstacle']
points_y = [i[1] for i in parsed_nodes.values() if i[2] == 'obstacle']
# print(f"{points_x = }\n{points_y = }")

for node in parsed_nodes.values():
    if node[2] == 'start':
        start_x = node[0]
        start_y = node[1]
    elif node[2] == 'target':
        target_x = node[0]
        target_y = node[1]

# safe nodes
# print(f"{waypoints = }")
safe_x = [i[0] for i in waypoints.values()]
safe_y = [i[1] for i in waypoints.values()]
names = [i for i in waypoints.keys()]
for i in range(len(waypoints)):
    x = safe_x[i]
    y = safe_y[i]
    plt.plot(x, y, marker='^', mfc=waypoint_col, mec=waypoint_col)
    plt.text(x + 0.1, y + 0.1, names[i])

# polygon sides
for side in nofly_region.sides:
    nofly_sides_x = []
    nofly_sides_y = []
    for point in side.points:
        nofly_sides_x.append(point.x)
        nofly_sides_y.append(point.y)
    plt.plot(nofly_sides_x, nofly_sides_y, res_col)
# print(f"{nofly_sides_x = }\n{nofly_sides_y = }")

# valid paths
# Set intersect_safe to either True or False to see both options.
connections, coords = tree.find_valid_connections(waypoints, nofly_region, margin_region, intersect_safe=INTERSECT_SAFE)
# print(f"{connections = }\n{coords = }")
for c in coords:
    paths_x = []
    paths_y = []
    paths_x.append(c[0][0])
    paths_y.append(c[0][1])
    paths_x.append(c[1][0])
    paths_y.append(c[1][1])
    plt.plot(paths_x, paths_y, linestyle=':', color='gray')

# plot
plt.plot(points_x, points_y, marker='o', mfc=res_col, mec=res_col, linestyle='None')
plt.plot(start_x, start_y, marker='X', mfc=start_col, mec=start_col)
plt.plot(target_x, target_y, marker='X', mfc=target_col, mec=target_col)
plt.axis('square')
plt.show()
