import csv
from itertools import combinations

import sympy as sp


def parse_data(filename: str):
    """
    Parses the given csv file so the data is more easily accessible later on.

    :param filename: Input .csv file with the header "waypoint_name, x_position, y_position, type".
    :return: A dictionary that stores each 'waypoint_name' as the key and a tuple (x_pos: float, y_pos: float,
        classification: string) as the value.
    """

    nodes = {}

    with open(filename, newline='') as infile:
        data_reader = csv.reader(infile)
        next(data_reader, None)  # skip the headers
        for row in data_reader:
            try:
                nodes[row[0]] = (
                float(row[1]), float(row[2]), row[3])  # nodes = {'waypoint_name': (x, y, classification)}
            except ValueError:
                print(f"ValueError occurred in parse_data for loop.")

    return nodes


def create_safe_waypoints(nodes: dict, margin: float = 1.3):
    """
    Apply a safety margin to nodes so connections_names can be made without being on the border of the restricted region,
    while preserving the name associated with each waypoint.

    :param nodes: A dictionary of nodes that has the form {'waypoint_name': (x, y, classification)}
    :param margin: Amount to scale the restricted region by to provide a safety margin so the drone doesn't
        accidentally enter the restricted region.
    :return: A dictionary containing each waypoint name and its corresponding safe waypoint. Also return the
        restricted_region polygon for later use.
    """

    # list of (x,y) of obstacle bounds
    restricted_vertices = [(node[0], node[1]) for node in nodes.values() if node[2] == 'obstacle']
    restricted_region = sp.convex_hull(*restricted_vertices)

    safe_waypoints = dict()
    # list of (x,y) of START and TARGET
    for name, data in nodes.items():
        if data[2] != 'obstacle':
            safe_waypoints[name] = (data[0], data[1])

    safe_region = restricted_region.scale(margin, margin, restricted_region.centroid)

    # ensure the safe_region is not so large that START or TARGET are inside
    # TODO: Ensure safe_region does not enclose START and TARGET

    # extend waypoints to also include safe vertices
    # IMPORTANT: this assumes that the order of points is maintained throughout this whole process.
    #   Only tested for first two nodes being START and TARGET and rest being OBSTACLE
    i = 0  # FIXME: there must be a better way to do this
    for name in nodes:
        if name not in safe_waypoints:
            try:
                safe_waypoints[name] = (safe_region.vertices[i].x, safe_region.vertices[i].y)
                i += 1
            except IndexError:
                # IMPORTANT: This is caused by the fact that the convex_hull ignores points that would make the polygon
                #   be not convex at any point. This should be fine since having that point in the polygon would be
                #   of no use since a path that goes there and then back to another point would not be optimal.
                print("IndexError occurred while making safe_waypoints dict.")
        else:
            pass

    # Move the target to the end of the dictionary
    safe_waypoints['T'] = safe_waypoints.pop('T')

    return safe_waypoints, restricted_region, safe_region


def find_valid_connections(safe_waypoints: dict, restricted_region: sp.Polygon, safe_region: sp.Polygon,
                           intersect_safe: bool = True):
    """
    Finds all connections_names between any two nodes in the given data that don't intersect the polygon bounded by the
    vertices labelled 'obstacle'. Also has the option to set `intersect_safe` to True, which will ensure that the paths
    drawn between nodes always respect the safety_margin, so no path goes too close to the restricted_region.

    :param intersect_safe: Whether to maintain safety margin on paths between nodes. True maintains margin.
    :param safe_region: The safe region created by scaling the restricted region.
    :param restricted_region: The region bounded by the 'obstacle' waypoints that must be avoided
    :param safe_waypoints: A dictionary of waypoints and their names that has the safety margin applied
    :return: A list containing every two points that can be connected without intersecting the restricted region. Each
        pair of points is a tuple containing the names of the parent and child waypoint that can be connected. Also
        returns a version with just the coordinates for easier use later on.
    """

    # gives a list of all possible combinations of points
    combos = list(combinations(safe_waypoints.values(), 2))

    valid_connections_names = []
    valid_connections_coords = []
    waypoint_names = list(safe_waypoints.keys())
    waypoint_values = list(safe_waypoints.values())

    for combo in combos:
        intersect_inner = sp.intersection(sp.Segment(*combo), restricted_region)
        intersect_outer = sp.intersection(sp.Segment(*combo), safe_region)
        if (not intersect_inner and not (len(intersect_outer) > 1)) or (not intersect_inner and not intersect_safe):
            first = waypoint_values.index(combo[0])
            second = waypoint_values.index(combo[1])
            # append ('first', 'second') to valid_connections_names
            valid_connections_names.append((waypoint_names[first], waypoint_names[second]))

            first = combo[0]
            second = combo[1]
            valid_connections_coords.append((first, second))

    return valid_connections_names, valid_connections_coords


def generate_tree(connections_names, connections_coords):
    """
    Generate the final tree to be used by the pathfinding algorithm.

    :param connections_coords: A list of tuples with node coordinates
    :param connections_names: Currently a list of tuples with node names (parent, child). Used for
        debugging/visualization purposes.
    :return: A dictionary containing each node and all nodes that can be reached through that node. Returns two dicts,
        one using node names for readability/debugging, and one using coordinates for later use. Both dictionaries are
        undirected.
        Important: The coordinates version, tree_coords is the final version of the tree/graph generated by this script.
        Any other calculations of distance, cost, etc. should be done in the pathfinding algorithm itself.
    """

    tree_names = {}
    tree_coords = {}

    # make tree using names
    for pair in connections_names:
        if pair[0] in tree_names:
            if not pair[1] in tree_names[pair[0]]:
                tree_names[pair[0]].append(pair[1])
        else:
            tree_names[pair[0]] = [pair[1]]

        if pair[1] in tree_names:
            if not pair[0] in tree_names[pair[1]]:
                tree_names[pair[1]].append(pair[0])
        else:
            tree_names[pair[1]] = list(pair[0])

    # make tree using coordinates
    for pair in connections_coords:
        if pair[0] in tree_coords:
            if not pair[1] in tree_coords[pair[0]]:
                tree_coords[pair[0]].append(pair[1])
        else:
            tree_coords[pair[0]] = list()
            tree_coords[pair[0]].append(pair[1])

        if pair[1] in tree_coords:
            if not pair[0] in tree_coords[pair[1]]:
                tree_coords[pair[1]].append(pair[0])
        else:
            tree_coords[pair[1]] = list()
            tree_coords[pair[1]].append(pair[0])

    return tree_names, tree_coords


if __name__ == "__main__":
    parsed_nodes = parse_data("randomdata.csv")

    waypoints, nofly_region, margin_region = create_safe_waypoints(parsed_nodes)

    connections, coords = find_valid_connections(waypoints, nofly_region, margin_region)
    # print(f"{connections = }\n{coords = }")

    final_tree_names, final_tree_coords = generate_tree(connections, coords)
    print(f"{final_tree_names = }\n{final_tree_coords = }")
