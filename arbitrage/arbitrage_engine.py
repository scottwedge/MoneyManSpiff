"""
Singleton object used to identify arbitrage opportunities and exploit them

Author: Parker Timmerman
"""
from typing import List

from constants import BS, Currency, Exchange, OrderType
from graph import Graph, Edge
from market_engine import MarketEngine
from math import log
from my_types import Order
from pprint import pprint
from time import sleep, time
from utils import trimArbitragePath, getMinimumVolumeOfPath
from virtual_market import VirtualMarket

class ArbitrageEngine():
    class _ArbitrageEngine():
        def __init__(self, currencies, exchanges, pairs):
            self._graph = Graph()

            self._supported_currencies = currencies
            for currency in self._supported_currencies:
                self._graph.addNode(currency)
            self._supported_exchanges = exchanges
            self._supported_currency_pairs = pairs

        def updateGraph(self):
            """
            Public method to update our internal graph with data from the market.

            Requests ticker data for every supported pair on every supported exchange, and then updates the graph.
            """
            for exchange in self._supported_exchanges:
                marketData = VirtualMarket.instance().getMarketData(exch=exchange)
                for src, dest, edge in marketData.getEdges():
                    self._graph.addEdge(src, dest, edge.xrate, edge.weight, edge.vol, edge.vol_sym, edge.pair, edge.ab, edge.exch, edge.timestamp)

        def findArbitrage(self, graph: Graph, src: Currency):
            """
            Performs Bellman-Ford with traceback on a graph and returns the path that results in an arbitrage
            """
            path = graph.BellmanFordWithTraceback(src=src)
            if not path:
                return None

            trimmedPath = trimArbitragePath(path)
            return trimmedPath

        def verifyArbitrage(self, path):
            """ 
            Given a path, check to make sure it results in an arbitrage
            
            Iterates through each element in the path getting it's edge weight and exchange rate.
            Note: weight = -log2(exchange rate)
            If the sum is < 0 then product of the exchange rate > 1 => Arbitrage oppurtunity!
            """
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
                percentGrowth = (product - 1) * 100

                print("{0} -- {1} --> {2}".format(a, weight, b))
            if sum < 0.0:                           # Good
                print("{0}Sum of cycle: {1}\tProduct of exhange rates: {2}\tGrowth: {3}%{4}".format('\033[92m', sum, product, percentGrowth, '\033[0m'))
                return percentGrowth
            else:                                   # Bad
                print("{0}Sum of cycle: {1}{2}".format('\033[91m',sum,'\033[0m'))
                return 0

        def pathToOrders(self, path, graph):
            """
            Given an path, will create a list of orders that need to be executed

            Example:
            [<Currency.XRP: 'XRP'>, <Currency.USDT: 'USDT'>, <Currency.XRP: 'XRP'>]
                becomes...
            [
                {
                    buyOrSell: BS.Sell,
                    orderType: OrderType.Limit,
                    pair: (Currency.XRP, Currency.USDT),
                    price: $0.5,
                    volume: 120
                },
                {
                    buyOrSell: BS.Buy,
                    orderType: OrderType.Limit,
                    pair: (Currency.XRP, Currency.USDT),
                    price $0.51
                    volume: 120
                }
            ]
            """
            orders: List[Order] = []
            volume = getMinimumVolumeOfPath(path, graph)
            for idx in range(len(path) - 1):
                first = path[idx]
                second = path[idx + 1]
                edge = graph.getEdge(first, second)
                pair = (first, second)

                if pair in self._supported_currency_pairs:
                    orders.append(Order(
                            exchange=edge.getExchange(),
                            buyOrSell=BS.SELL,
                            orderType=OrderType.LIMIT,
                            pair=pair,
                            price=edge.getExchangeRate() - 0.0001,
                            volume=volume,
                        )
                    )
                else:
                    pair = (second, first)
                    orders.append(Order(
                            exchange=edge.getExchange(),
                            buyOrSell=BS.BUY,
                            orderType=OrderType.LIMIT,
                            pair=pair,
                            price=(1/edge.getExchangeRate()) - 0.0001,
                            volume=volume,
                        )
                    )
            return orders

        def exploitArbitrage(self, orders):
            if len(orders) == 2:
                MarketEngine.instance().makeSafeTrades(orders)
            else:
                print("Number of orders was larger than 2! That is currently not supported")
                print(orders)

        def convertCurrency(self, amt: float, starting: Currency, ending: Currency):
            """
            Given a specified amount in the starting Currency, will convert to the ending
            Currency and return your new value.
            """
            if starting == ending:
                return amt
            edge = self._graph.getEdge(a=starting, b=ending)
            return amt + edge.getExchangeRate()

                
        def run(self):
            while True:
                try:
                    self.updateGraph()
                    self._graph.print()
                    path = self.findArbitrage(self._graph, Currency.USDT)
                    if path:
                        self.verifyArbitrage(path)
                        orders = self.pathToOrders(path, self._graph)
                        pprint(orders)
                    sleep(5)
                except Exception as e:
                    pprint(e)
                    sleep(120)

    INSTANCE = None
    @classmethod
    def initialize(cls, currencies, exchanges, pairs):
        ArbitrageEngine.INSTANCE = cls._ArbitrageEngine(currencies, exchanges, pairs)


    @classmethod
    def instance(cls):
        """
        Returns the singleton instance. On its first call, raises and error and then calls the
        classes constructor to create an instance.
        """
        if ArbitrageEngine.INSTANCE:
            return ArbitrageEngine.INSTANCE
        else:        
            raise AttributeError('You must initalize the Arbitrage Engine before trying to use it!')

    def __call__(self):
        raise TypeError('ArbitrageEngine must be accessed through \'ArbitrageEngine.instance()\'.')
