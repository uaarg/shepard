import math
def dijkstra(conns, coords):
    destinationNode = "T"
    startNode = "S"
    visitedNodes = {}
    distances = {}
    for i in conns:
        if i[0] not in visitedNodes:
            visitedNodes[i[0]] = False
        if i[1] not in visitedNodes:
            visitedNodes[i[1]] = False
    distances['S'] = 0

    for i in visitedNodes:
        if i != 'S':
            distances[i] = 999999
    
    currentNode = 'S'
    while(visitedNodes['T'] == False):
        print("new visitedNode")
        print(currentNode)
        for i in range(len(conns)):
            if conns[i][0] == currentNode:
                if visitedNodes[conns[i][1]] == False:
                    point1 = coords[i][0]
                    point2 = coords[i][1]
                    dist = math.sqrt(((point1[0]-point2[0])**2) + ((point1[1]-point2[1])**2))
                    print("updating distance between" + conns[i][0] + "and " + conns[i][1])
                    distances[conns[i][1]] = min(dist, distances[conns[i][1]])
                    print(min(dist, distances[conns[i][1]])) 
        visitedNodes[currentNode] = True
        minDist = 999999
        for i in visitedNodes:
            if not visitedNodes[i]:
                minDist = min(distances[i], minDist)
        node = None
        for i in distances:
            if distances[i] == minDist:
                node = i
        currentNode = node
    print(distances)
    
