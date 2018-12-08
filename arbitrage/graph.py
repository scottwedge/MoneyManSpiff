"""
Graph objects used for Money Man Spiff's arbitrage engine
At it's core is a 2D Dictionary aka Dictionary of Dictionaries

Author: Parker Timmerman
"""
from decimal import *
from sys import float_info
from typing import List, Tuple

MAX_FLOAT = float_info.max

class Edge():
    """ An edge object to be used for arbitrage """

    def __init__(self, xrate, weight, vol, vol_sym, pair, ab, exch, timestamp):
        self.xrate = xrate                      # exchange rate from the market, generally bid or 1/ask
        self.weight = weight                    # edge weight used for neg cycle detection, -log(xrate)
        self.vol = vol                          # volume associated with bid or ask price
        self.vol_sym = vol_sym                  # currency which the volume is in terms of
        self.pair = pair
        self.ab = ab                            # ask or buy price
        self.exch = exch                        # echange for which this edge comes from
        self.timestamp = timestamp

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
    def setAskOrBid(self, ab):
        self.ab = ab

    def Volume(self):
        return (self.vol, self.vol_sym)

    def getExchange(self):
        return self.exch

    def getTimestamp(self):
        return self.timestamp

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

    def addEdge(self, src, dest, xrate, weight, vol, vol_sym, pair, ab, exch, timestamp) -> bool:
        """ Add an edge to the graph """
        if src not in self.G:
            print("Source node ({}) does not exist!".format(src))
            return False
        if dest not in self.G:
            print("Destination node ({}) does not exist!".format(dest))
            return False
        if dest not in self.G[src]:
            self.G[src][dest] = Edge(xrate, weight, vol, vol_sym, pair, ab, exch, timestamp)
        elif timestamp > self.G[src][dest].getTimestamp():
            # If the given edge is newer than the existing, replace it, no questions asked
            self.G[src][dest] = Edge(xrate, weight, vol, vol_sym, pair, ab, exch, timestamp)
            return True
        elif weight < self.G[src][dest].getWeight():
            # An edge already exists with the same timestamp, but we found an edge with a lower weight!
            self.G[src][dest] = Edge(xrate, weight, vol, vol_sym, pair, ab, exch, timestamp)
            return True
        # If we reach here it means the edge we were trying to update is from the same cycle
        # and we already had an edge that was cheaper
        return False
    
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

    def getWeights(self) -> List[Tuple[str, str, float]]:
        """ Returns a list of tuples in the following format (first node, second node, arbitrage weight) """
        return list([(src, dest, self.G[src][dest].getWeight()) for src in self.G.keys() for dest in self.G[src].keys()])

    def print(self):
        """ String representation of the graph """
        for src in self.G.keys():
            print("{}:".format(src))
            for dest in self.G[src].keys():
                print("\t{0} -- weight: {1} on {2} --> {3}".format(src, self.G[src][dest].getWeight(), 
                                                                   self.G[src][dest].getExchange(), dest)
                    )

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

    def BellmanFordWithTraceback(self, src):
        """ Perform Bellman-Ford on graph and test for negative cycle """

        # Initalize distance to all nodes to be infinity, then set distance to souce node to be 0
        dist = {node: MAX_FLOAT for node in self.G.keys()}
        pred = {node: None for node in self.G.keys()}
        dist[src] = 0
        num_nodes = len(self.G.keys())

        # Find shortest path
        for _ in range (num_nodes - 1):
            for u, v, w, in self.getWeights():
                if dist[u] != MAX_FLOAT and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    pred[v] = u
       
        # This is a really slow way to find negative cycles, but ya gotta start somewhere
        # Loop for number of edges
        for u, v, w in self.getWeights():
            if dist[u] != MAX_FLOAT and dist[u] + w + 0.001 < dist[v]:
                # print("Graph contains a negative cycle!")
                return self.traceback(v, pred)
