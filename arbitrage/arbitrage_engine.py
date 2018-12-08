"""
Singleton object used to identify arbitrage oppurtunities and exploit them

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
                marketData = VirtualMarket.instance().getArbitrageWeights(exch=exchange)
                for currencyPairAndWeight in marketData:
                    first = currencyPairAndWeight[0]
                    second = currencyPairAndWeight[1]
            
                    self._graph.addEdge(first, second, 0, weight, 0, pair[0], pair, 'bid', exchange, timestamp)
                    self._graph.addEdge(pair[1], pair[0], 1/ask, weight2, ask_vol, pair[0], pair, 'ask', exchange, timestamp)

        def findArbitrage(self, graph: Graph, src: Currency):
            """
            Performs Bellman-Ford with traceback on a graph and returns the path that results in an arbitrage
            """
            path = graph.BellmanFordWithTraceback(src=src)
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

                print("{0} -- {1} --> {2}".format(a, weight, b))
            if sum < 0.0:                           # Good
                print("{0}Sum of cycle: {1}\tProduct of exhange rates: {2}{3}".format('\033[92m',sum,product,'\033[0m'))
            else:                                   # Bad
                print("{0}Sum of cycle: {1}{2}".format('\033[91m',sum,'\033[0m'))

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