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
