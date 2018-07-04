"""
Arbitrage Trading engine for Money Man Spiff's arbitrage program

Uses the Kraken Exchange API to make trades, and data from the Graph class to exploit arbitrage oppurtunities

Author: Parker Timmerman
"""

from requests.exceptions import HTTPError
from graph import Graph, Edge
from decimal import *
import math
import krakenex

class Trade():
    """ An object that contains all of the necessary information to make a trade """

    def __init__(self, pair, bs, price):
        self.pair = pair
        self.bs = bs                # buy or sell, a string
        self.price = price

    # Getters and Setters
    def getPair(self):
        return self.pair
    def setPair(self, pair):
        self.pair = pair

    def getBuyOrSell(self):
        return self.bs
    def setBuyOrSell(self, bs):
        self.bs = bs

    def getPrice(self):
        return self.price
    def setPrice(self, price):
        self.price = price

class ArbitrageEngine():

    def __init__(self):
        self.K = krakenex.API()
        self.K.load_key('kraken.key')

    def currencyConversion(self, a1, a2, amt, graph):
        """ Given two currencies, convert from one (a1) to the other (a2) """
        if a1 == a2:
            return amt

        e = graph.getEdge(a1, a2) 
        if e is None:                               # If the edge doesnt exist, convert from a1 --> BTC ---> a2
            print("Had to convert to BTC")
            e1 = graph.getEdge(a1, 'XBT')
            e2 = graph.getEdge('XBT', a2)
            return amt * e1.getExchangeRate() * e2.getExchangeRate()

        return e.getExchangeRate() * amt

    def makeTrade(self, trade) -> bool:
        """ Given a tade, make it, then return true or false """

    def exploitArbitrage(self, graph, path):
        """ Given a graph, and a path that is a negative cycle/arbitrage, exploit it! """

        #bal = self.K.query_private('Balance')       # current account balance
        vol_sym = path[0]                            # want to get all of the volumes in terms of the first currency
        vols = [0] * (len(path) - 1)                 # volumes of all pairs in said currency

        product = 1
        for idx in range(len(path) - 1):
            a = path[idx]
            b = path[idx + 1]

            edge = graph.getEdge(a, b)
            v = edge.getVolume()
            vs = edge.getVolumeSymbol()
            vols[idx] = self.currencyConversion(vs, vol_sym, v, graph)
            print("{0} -- vol: {1} units of {2} ({3} units of {4}) --> {5}".format(a, v, vs, vols[idx], vol_sym, b))

            product = product * edge.getExchangeRate()

        min_vol = min(vols)
        usd_vol = self.currencyConversion(vol_sym, 'USD', min_vol, graph)
        opp = usd_vol * product
        profit = opp - usd_vol
        print("Min Volume: {0}, maximum arbitrage oppurtunity: {1} USD, profit {2} USD".format(min_vol, opp, profit))
        
        
