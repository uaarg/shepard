import re


def re_search(pattern, text):
    try:
        match = re.search(pattern, text, re.IGNORECASE)
        match = match.group()
    except AttributeError:
        print("ERROR: match not found.")
        exit(1)
    return match


def parse_task1_route(qr_text: str):
    route_pattern = r"(?<=follow route: )(\w+(?:; \w+)*)?"
    route = re_search(route_pattern, qr_text)
    route = re.sub(";", "", route)
    route_list = route.split(" ")
    return route_list


def parse_task1_avoidance(qr_text: str):
    rejoin_point_pattern = r"(?<=rejoin the route at )(\w+)"
    region_points_pattern = r"(?<=Avoid the area bounded by: )(\w+(?:; \w+)*)?"

    rejoin_point = re_search(rejoin_point_pattern, qr_text)
    region_points = re_search(region_points_pattern, qr_text)
    region_points = re.sub(";", "", region_points)
    region_points_list = region_points.split(" ")

    return region_points_list, rejoin_point


if __name__ == "__main__":
    task1_route = parse_task1_route("Follow route: Quebec; Lima; Alpha; Tango")
    region, rejoin_point = parse_task1_avoidance("Avoid the area bounded by: Zulu; Bravo; Tango; Uniform.  Rejoin the route at Lima")

    print(f"{task1_route = }")
    print(f"{region = }")
    print(f"{rejoin_point = }")
