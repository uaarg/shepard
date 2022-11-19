import numpy as np


# PARAMETERS
NUM_VERTICES = 10
FILENAME = "randomdata"  # without .csv

start = (0, 0)
target = (20, 20)

low = 3
high = 17

# number of vertices to generate
n_vertices = NUM_VERTICES

random_nums = low + (high - low) * np.random.rand(2, n_vertices)

x_vals = random_nums[0]
y_vals = random_nums[1]

with open(f"{FILENAME}.csv", 'w') as datafile:
    datafile.write("waypoint_name,x_position,y_position,classification\n")

    datafile.write(f"S,{start[0]},{start[1]},start\n")
    datafile.write(f"T,{target[0]},{target[1]},target\n")

    for i in range(n_vertices):
        datafile.write(f"{i},{x_vals[i]},{y_vals[i]},obstacle\n")
