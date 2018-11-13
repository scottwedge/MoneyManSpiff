"""
Singleton object used to identify arbitrage oppurtunities and exploit them

Author: Parker Timmerman
"""

from constants import Currency, Exchange
from graph import Graph, Edge
from market_engine import MarketEngine
from math import log
from pprint import pprint
from time import sleep, time
from util import trimPath

class ArbitrageEngine():
    class _ArbitrageEngine():
        def __init__(self):
            self._graph = Graph()

            self._supported_currencies = MarketEngine.instance().supportedCurrencies()
            for currency in self._supported_currencies:
                self._graph.addNode(currency)
            self._supported_exchanges = MarketEngine.instance().supportedExchanges()
            self._supported_currency_pairs = MarketEngine.instance().supportedCurrencyPairs()

        def updateGraph(self):
            """
            Public method to update our internal graph with data from the market.

            Requests ticker data for every supported pair on every supported exchange, and then updates the graph.
            """
            timestamp = int(time())  # Stamp each request with the local time which we requested it
            for exchange in self._supported_exchanges:
                tickerInfos = MarketEngine.instance().fetchTickers(
                    exch=exchange,
                    pairs=self._supported_currency_pairs
                )
                for tickerInfo in tickerInfos.items():
                    pair = tickerInfo[0]

                    ask = float(tickerInfo[1]['ask'])
                    bid = float(tickerInfo[1]['bid'])
                    ask_vol = float(tickerInfo[1]['ask_vol'])
                    bid_vol = float(tickerInfo[1]['bid_vol'])

                    weight1 = -(log(bid, 2))
                    weight2 = -(log((1/ask), 2))
            
                    self._graph.addEdge(pair[0], pair[1], bid, weight1, bid_vol, pair[0], pair, 'bid', exchange, timestamp)
                    self._graph.addEdge(pair[1], pair[0], 1/ask, weight2, ask_vol, pair[0], pair, 'ask', exchange, timestamp)

        def findArbitrage(self):
            """
            Performs Bellman-Ford with traceback on our graph and returns the path that results in an arbitrage
            """
            path = self._graph.BellmanFordWithTraceback(src=Currency.USDT)

            


        def verifyArbitrage(self, path):
            """ Given a path, check to make sure it results in an arbitrage """
            start = path[0]
            while not path[-1] == start:            # remove unnecessary currencies from path
                path.remove(path[-1])
            print(path)

            sum = 0
            product = 1
            for idx in range(len(path) - 1):
                a = path[idx]
                b = path[idx + 1]
                edge = self._graph.getEdge(a, b)

                weight = edge.getWeight()           # get the edge weight to verify sum of path < 0
                sum += weight

                xrate = edge.getExchangeRate()      # multiply all exhange rates to verify product > 1
                product = product * xrate

                print("{0} -- {1} --> {2}".format(a, weight, b))
            if sum < 0.0:                           # Good
                print("{0}Sum of cycle: {1}\tProduct of exhange rates: {2}{3}".format('\033[92m',sum,product,'\033[0m'))
            else:                                   # Bad
                print("{0}Sum of cycle: {1}{2}".format('\033[91m',sum,'\033[0m'))

        def run(self):
            while True:
                try:
                    self.updateGraph()
                    self._graph.print()
                    path = self._graph.BellmanFord(Currency.USDT)
                    if path:
                        self.verifyArbitrage(path)
                    sleep(5)
                except Exception as e:
                    pprint(e)
                    sleep(120)

    INSTANCE = None
    @classmethod
    def instance(cls):
        """
        Returns the singleton instance. On its first call, raises and error and then calls the
        classes constructor to create an instance.
        """
        if ArbitrageEngine.INSTANCE:
            return ArbitrageEngine.INSTANCE
        else:
            ArbitrageEngine.INSTANCE = cls._ArbitrageEngine()
            return ArbitrageEngine.INSTANCE

    def __call__(self):
        raise TypeError('ArbitrageEngine must be accessed through \'ArbitrageEngine.instance()\'.')