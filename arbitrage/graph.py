"""
Graph objects used for Money Man Spiff's arbitrage engine
At it's core is a 2D Dictionary aka Dictionary of Dictionaries

Author: Parker Timmerman
"""
from typing import List, Tuple
from decimal import *

class Edge():
    """ An edge object to be used for arbitrage """

    def __init__(self, xrate, weight, vol, vol_sym, pair, ab):
        self.xrate = xrate                      # exchange rate from the market, generally bid or 1/ask
        self.weight = weight                    # edge weight used for neg cycle detection, -log(xrate)
        self.vol = vol                          # volume associated with bid or ask price
        self.vol_sym = vol_sym                  # currency which the volume is in terms of
        self.pair = pair
        self.ab = ab

    # Getters and Setters
    def getExchangeRate(self):
        return self.xrate
    def setExchangeRate(self, xrate):           # Note: Exchange rate and weight should always be changed together
        self.xrate = xrate                      # because weight is a derivative of exhange rate

    def getWeight(self):
        return self.weight
    def setWeight(self, weight):
        self.weight = weight
    
    def getVolume(self):
        return self.vol
    def setVolume(self, vol):
        self.vol = vol

    def getVolumeSymbol(self):
        return self.vol_sym
    def setVolumeSymbol(self, vol_sym):
        self.vol_sym = vol_sym
    
    def getPair(self):
        return self.pair
    def setPair(self, pair):
        self.pair = pair

    def getAskOrBid(self):
        return self.ab
    def setAskOrBuy(self, ab):
        self.ab = ab

    def Volume(self):
        return (vol, vol_sym)

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

    def addEdge(self, src, dest, xrate, weight, vol, vol_sym, pair, ab) -> bool:
        """ Add an edge to the graph """
        if src not in self.G:
            print("Source node ({}) does not exist!".format(src))
            return False
        if dest not in self.G:
            print("Destination node ({}) does not exist!".format(dest))
            return False

        self.G[src][dest] = Edge(xrate, weight, vol, vol_sym, pair, ab)           # Src and dest must exist so add the edge
        return True

    def updateEdge(self, src, dest, xrate, weight, vol, vol_sym, pair, ab) -> bool:
        """ Update an edge weight between two nodes """
        if src not in self.G:
            print("Source node ({}) does not exist!".format(src))
            return False
        if dest not in self.G:
            print("Destination node ({}) does not exist!".format(dest))
            return False
        
        self.G[src][dest] = Edge(xrate, weight, vol, vol_sym, pair, ab)
        return True
    
    def getEdge(self, a, b):
        """ Get the edge from a to b """
        if b not in self.G[a]:
            print("Edge between {0} and {1} does not exist!".format(a, b))
            return
        else:
            return self.G[a][b]

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

    def traceback(self, start, preds):
        """ Given a starting node and a dictionary of predecessors, performs a traceback to ID a negative loop """
        traveled = {node: False for node in self.G.keys()}
        path = []

        def aux(start, traveled, preds, path):
            if traveled[start] == True:
                path.append(start)
                return list(reversed(path))
            else:
                traveled[start] = True
                path.append(start)
                return aux(preds[start], traveled, preds, path)

        return aux(start, traveled, preds, path)

    def BellmanFord(self, src):
        """ Perform Bellman-Ford on graph and test for negative cycle """

        # Initalize distance to all nodes to be infinity, then set distance to souce node to be 0
        dist = {node: Decimal('Infinity') for node in self.G.keys()}
        pred = {node: None for node in self.G.keys()}
        dist[src] = 0
        num_nodes = len(self.G.keys())

        # Find shortest path
        for i in range (num_nodes - 1):
            for u, v, edge, in self.getEdges():
                w = edge.getWeight()
                if dist[u] != Decimal("Infinity") and dist[u] + w + Decimal('0.0004') < dist[v]:
                    dist[v] = dist[u] + w
                    pred[v] = u
       
        # Detect negative cycle
        for u, v, edge in self.getEdges():
            w = edge.getWeight()
            if dist[u] != Decimal("Infinity") and dist[u] + w + Decimal('0.0004') < dist[v]:
                print("Graph contains a negative cycle!")
                return self.traceback(v, pred)

