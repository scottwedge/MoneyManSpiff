"""
Arbitrage Trading engine for Money Man Spiff's arbitrage program

Uses the Kraken Exchange API to make trades, and data from the Graph class to exploit arbitrage oppurtunities

Author: Parker Timmerman
"""

from requests.exceptions import HTTPError
from graph import Graph, Edge
from decimal import *
import krakenex

class ArbitrageEngine():

    def __init__(self):
        self.K = krakenex.API()
        K.load_key('kraken.key')

    def exploitArbitrage(self, graph, path):
        """ Given a graph, and a path that is a negative cycle/arbitrage, exploit it! """

        bal = K.query_private('Balance')        # current account balance
        vol_sym = path[0]                       # want to get all of the volumes in terms of the first currency
        vols = []                               # volumes of all pairs

        
