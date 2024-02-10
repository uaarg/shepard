#let the present location be (0,0)
#we pass in the length of the side of the square cam area
#we pass in the number of loops around the origin, and has a default value of 20


def landingspot(a, number_of_loops=20):
    route = []
    x, y = 0, 0
    for i in range(2, number_of_loops, 2):

        for j in range(4):
            if j == 0:
                y = y - a
                route.append([x, y])
                for k in range(i - 1):
                    x = x + a
                    route.append([x, y])
            if j == 1:
                for k in range(i):
                    y = y + a
                    route.append([x, y])
            if j == 2:
                for k in range(i):
                    x = x - a
                    route.append([x, y])
            if j == 3:
                for k in range(i):
                    y = y - a
                    route.append([x, y])
    print(route)


landingspot(1, 15)
