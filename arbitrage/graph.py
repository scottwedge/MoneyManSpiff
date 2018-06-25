"""
Graph objects used for Money Man Spiff's arbitrage engine
At it's core is a 2D Dictionary/Dictionary of Dictionaries

Author: Parker Timmerman
"""
from typing import List, Tuple

class Graph():
    """ A graph data structure represented as a 2D Dictionary"""

    def __init__(self):
        self.G = {}

    def addNode(self, name) -> bool:
        """ Add a node to the graph, if the node already exists, return false """
        if name in self.G:
            print("Node already exists!")
            return False
        else:
            self.G[name] = {}
        return True

    def addEdge(self, src, dest, weight) -> bool:
        """ Add an edge to the graph """
        if src not in self.G:
            print("Source node ({}) does not exist!".format(src))
            return False
        if dest not in self.G:
            print("Destination node ({}) does not exist!".format(dest))
            return False

        self.G[src][dest] = weight                      # Src and dest must exist so add the edge
        return True

    def updateEdge(self, src, dest, weight) -> bool:
        """ Update an edge weight between two nodes """
        if src not in self.G:
            print("Source node ({}) does not exist!".format(src))
            return False
        if dest not in self.G:
            print("Destination node ({}) does not exist!".format(dest))
            return False
        
        self.G[src][dest] = weight
        return True

    def getNodes(self) -> List[str]:
        """" Returns a list of all the nodes in the graph """
        return list(self.G.keys())

    def getEdges(self) -> List[Tuple[str, str, float]]:
        """ Returns a list of all the edges in the graph, represented as tuples """
        return list([(src, dest, self.G[src][dest]) for src in self.G.keys() for dest in self.G[src].keys()])

    def print(self):
        """ String representation of the graph """
        for src in self.G.keys():
            print("{}:".format(src))
            for dest in self.G[src].keys():
                print("\t{0} -- weight: {1} --> {2}".format(src, self.G[src][dest], dest))

    def BellmanFord(self, src):
        """ Perform Bellman-Ford on graph and test for negative cycle """

        # Initalize distance to all nodes to be infinity, then set distance to souce node to be 0
        dist = {node: float('Inf') for node in self.G.keys()}
        dist[src] = 0




