"""
Singleton object that is a virtual representation of the market

Author: Parker Timmerman
"""

from constants import Currency, Exchange
from graph import Graph, Edge
from math import log
from time import time

class VirtualMarket():
    class _VirtualMarket():
        def __init__(self):
            """
            Example of market:
            {
                Exchange.KRAKEN: {
                    Graph representing the Kraken market
                },
                Exchange.BINANCE: {
                    Graph representing the Binance market
                }
            }
            """
            self._market = {}

            self._supportedExchanges = [
                Exchange.BINANCE,
                Exchange.KRAKEN,
            ]

#                Currency.XRP,
            self._supportedCurrencies = [
                Currency.ETH,
                Currency.USDT,
            ]

#                (Currency.XRP, Currency.USDT),
            self._supportedCurrencyPairs = [
                (Currency.ETH, Currency.USDT),
            ]
            self._initMarket()

        def _initMarket(self):
            for exchange in self._supportedExchanges:
                graph = Graph()
                for currency in self._supportedCurrencies:
                    graph.addNode(currency)
                self._market[exchange] = graph

        def updateExchange(self, exch: Exchange, marketData, timestamp = None):
            """
            Given an exchange, and market data in the form of:
            {
                (<Currency.XRP: 'XRP'>, <Currency.USDT: 'USDT'>): {'ask': '0.51003000', 'bid': '0.50960000', 'ask_vol': '195.000', 'bid_vol': '30.000'},
                (<Currency.EOS: 'EOS'>, <Currency.USDT: 'USDT'>): {'ask': '0.51003000', 'bid': '0.50960000', 'ask_vol': '195.000', 'bid_vol': '30.000'}
            }
            Update the graph for the given exchange
            """
            if not exch in self._market:
                raise TypeError('{} is not in the market representation, it must not be supported!')
            else:
                if not timestamp:
                    timestamp = int(time())  # Stamp each request with the local time which we requested it
                for pairInfo in marketData.items():
                    pair = pairInfo[0]

                    ask = pairInfo[1]['ask']
                    bid = pairInfo[1]['bid']
                    ask_vol = pairInfo[1]['ask_vol']
                    bid_vol = pairInfo[1]['bid_vol']

                    weight1 = -(log(bid, 2))
                    weight2 = -(log((1/ask), 2))

                    self._market[exch].addEdge(pair[0], pair[1], bid, weight1, bid_vol, pair[0], pair, 'bid', exch, timestamp)
                    self._market[exch].addEdge(pair[1], pair[0], 1/ask, weight2, ask_vol, pair[0], pair, 'ask', exch, timestamp)

        def updateMarket(self, marketData):
            """
            Given market data in the form of:
            {
                Exchange.KRAKEN:
                {
                    ...
                },
                Exchange.BINANCE:
                {
                    ...
                },
            }
            """
            timestamp = int(time())
            for exchange in marketData.keys():
                self.updateExchange(exch=exchange, marketData=marketData[exchange], timestamp=timestamp)


        def getArbitrageWeights(self, exch: Exchange):
            """
            Given an exchange, returns a dictionary of node pairs (currencies) to the -log(exchange rate)
            """
            weights = {}
            exchangeData = self._market[exch]
            for weight in exchangeData.getWeights():
                weights[(weight[0], weight[1])] = weight[2]
            return weights

        def getMarketData(self, exch: Exchange):
            """
            Given an exchange, returns a dictionary that is market data for the exchange
            """
            return self._market[exch]

        def convertCurrency(self, exch: Exchange, amt: float, start: Currency, end: Currency):
            """
            Given an exchange, an amount, starting currency, and an ending currency, will convert
            the amount in terms of the start currency to an amount in terms of the end currency
            """
            if (start == end):
                return amt
                
            exchangeGraph = self._market[exch]
            pairEdge = exchangeGraph.getEdge(start, end)
            return amt * pairEdge.getExchangeRate()
                


    INSTANCE = None
    @classmethod
    def instance(cls):
        """
        Returns the singleton instance. On its first call, raises and error and then calls the
        classes constructor to create an instance.
        """
        if VirtualMarket.INSTANCE:
            return VirtualMarket.INSTANCE
        else:
            VirtualMarket.INSTANCE = cls._VirtualMarket()
            return VirtualMarket.INSTANCE

    def __call__(self):
        raise TypeError('VirtualMarket must be accessed through \'VirtualMarket.instance()\'.')