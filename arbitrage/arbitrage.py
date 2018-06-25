"""
Core python script for Money Man Spiff's arbitrage

Uses the Kraken Exchange API to get data, and the Graph class to detect negative cycles

Author: Parker Timmerman
"""

from requests.exceptions import HTTPError
from graph import Graph
from math import log
import krakenex
import pprint

ASSETS = ['XBT', 'LTC', 'XDG', 'REP', 'XRP', 'XLM', 'ETH', 'ETC', 'ICN', 'USDT', 'DASH', 'ZEC', 'XMR', 'GNO', 'EOS', 'BCH', 'MLN', 'EUR', 'USD', 'JPY', 'CAD', 'GBP']
ASSET_PAIRS = ['BCH/EUR', 'BCH/USD', 'BCH/XBT', 'DASH/EUR', 'DASH/USD', 'DASH/XBT', 'EOS/ETH', 'EOS/EUR', 'EOS/USD', 'EOS/XBT', 'GNO/ETH', 'GNO/EUR', 'GNO/USD', 'GNO/XBT', 'USDT/USD', 'ETC/ETH', 'ETC/XBT', 'ETC/EUR', 'ETC/USD', 'ETH/XBT', 'ETH/CAD', 'ETH/EUR', 'ETH/GBP', 'ETH/JPY', 'ETH/USD', 'ICN/ETH', 'ICN/XBT', 'LTC/XBT', 'LTC/EUR', 'LTC/USD', 'MLN/ETH', 'MLN/XBT', 'REP/ETH', 'REP/XBT', 'REP/EUR', 'REP/USD', 'XBT/CAD', 'XBT/EUR', 'XBT/GBP', 'XBT/JPY', 'XBT/USD', 'XDG/XBT', 'XLM/XBT', 'XLM/EUR', 'XLM/USD', 'XMR/XBT', 'XMR/EUR', 'XMR/USD', 'XRP/XBT', 'XRP/CAD', 'XRP/EUR', 'XRP/JPY', 'XRP/USD', 'ZEC/XBT', 'ZEC/EUR', 'ZEC/JPY', 'ZEC/USD']
ALT_NAME_TRANS = {'BCHEUR': ('BCH', 'EUR'),
                    'BCHUSD': ('BCH', 'USD'),
                    'BCHXBT': ('BCH', 'XBT'),
                    'DASHEUR': ('DASH', 'EUR'),
                    'DASHUSD': ('DASH', 'USD'),
                    'DASHXBT': ('DASH', 'XBT'),
                    'EOSETH': ('EOS', 'ETH'),
                    'EOSEUR': ('EOS', 'EUR'),
                    'EOSUSD': ('EOS', 'USD'),
                    'EOSXBT': ('EOS', 'XBT'),
                    'GNOETH': ('GNO', 'ETH'),
                    'GNOEUR': ('GNO', 'EUR'),
                    'GNOUSD': ('GNO', 'USD'),
                    'GNOXBT': ('GNO', 'XBT'),
                    'USDTZUSD': ('USDT', 'USD'),
                    'XETCXETH': ('ETC', 'ETH'),
                    'XETCXXBT': ('ETC', 'XBT'),
                    'XETCZEUR': ('ETC', 'EUR'),
                    'XETCZUSD': ('ETC', 'USD'),
                    'XETHXXBT': ('ETH', 'XBT'),
                    'XETHZCAD': ('ETH', 'CAD'),
                    'XETHZEUR': ('ETH', 'EUR'),
                    'XETHZGBP': ('ETH', 'GBP'),
                    'XETHZJPY': ('ETH', 'JPY'),
                    'XETHZUSD': ('ETH', 'USD'),
                    'XICNXETH': ('ICN', 'ETH'),
                    'XICNXXBT': ('ICN', 'XBT'),
                    'XLTCXXBT': ('LTC', 'XBT'),
                    'XLTCZEUR': ('LTC', 'EUR'),
                    'XLTCZUSD': ('LTC', 'USD'),
                    'XMLNXETH': ('MLN', 'ETH'),
                    'XMLNXXBT': ('MLN', 'XBT'),
                    'XREPXETH': ('REP', 'ETH'),
                    'XREPXXBT': ('REP', 'XBT'),
                    'XREPZEUR': ('REP', 'EUR'),
                    'XREPZUSD': ('REP', 'USD'),
                    'XXBTZCAD': ('XBT', 'CAD'),
                    'XXBTZEUR': ('XBT', 'EUR'),
                    'XXBTZGBP': ('XBT', 'GBP'),
                    'XXBTZJPY': ('XBT', 'JPY'),
                    'XXBTZUSD': ('XBT', 'USD'),
                    'XXDGXXBT': ('XDG', 'XBT'),
                    'XXLMXXBT': ('XLM', 'XBT'),
                    'XXLMZEUR': ('XLM', 'EUR'),
                    'XXLMZUSD': ('XLM', 'USD'),
                    'XXMRXXBT': ('XMR', 'XBT'),
                    'XXMRZEUR': ('XMR', 'EUR'),
                    'XXMRZUSD': ('XMR', 'USD'),
                    'XXRPXXBT': ('XRP', 'XBT'),
                    'XXRPZCAD': ('XRP', 'CAD'),
                    'XXRPZEUR': ('XRP', 'EUR'),
                    'XXRPZJPY': ('XRP', 'JPY'),
                    'XXRPZUSD': ('XRP', 'USD'),
                    'XZECXXBT': ('ZEC', 'XBT'),
                    'XZECZEUR': ('ZEC', 'EUR'),
                    'XZECZJPY': ('ZEC', 'JPY'), 
                    'XZECZUSD': ('ZEC', 'USD')}

DELM = '/'

# Convinence Functions
def splitPair(pair, delm) -> (str, str):
    """ Given a currency pair and a delimiter, splits the pair """
    idx = pair.index(delm)
    a1 = pair[:idx]
    a2 = pair[idx + 1:]
    return a1, a2

class Pipeline():
    
    def __init__(self):
        """ Initialize the graph, open a connection to the API, and build Ticker string for querying to the API """
        self.G = Graph()
        self.K = krakenex.API()

        # Take the asset pairs, remove the '/' and make the list comma seperated so you can ask the API for the data
        self.TICKER_PAIRS = ",".join([pair.replace('/', '') for pair in ASSET_PAIRS])
        print(self.TICKER_PAIRS)

    def initGraph(self):
        """ Initialize the graph's nodes, and edges. Set all edge weights to 0 """
        # Initialize graph with nodes
        for asset in ASSETS:
            self.G.addNode(asset)

        # Initialize graph with weights of 0
        for pair in ASSET_PAIRS:
            a1, a2 = splitPair(pair, DELM)
            self.G.addEdge(a1, a2, 0)
            self.G.addEdge(a2, a1, 0)

    def getTickerData(self, pairs):
        """ Given a comma seperated list of pairs, get the ticker information from the API """
        resp = self.K.query_public('Ticker', {'pair': pairs})
        if not resp['error'] == []:
            pprint.pprint(resp['error'])
        else:
            return resp['result']

    def updateGraph(self, data):
        """ Given data from the API update the edge weights of the graph """
        for item in data.items():
            name = item[0]
            if ALT_NAME_TRANS.get(name):
                a1, a2 = ALT_NAME_TRANS.get(name)
                w = -log(float(item[1]['a'][0]), 2)
                self.G.updateEdge(a1, a2, w)
                self.G.updateEdge(a2, a1, (1/w))

    def run(self):
        # Initialize graph
        self.initGraph()
        data = self.getTickerData(self.TICKER_PAIRS)
        self.updateGraph(data)

        self.G.print()

if __name__ == '__main__':
    p = Pipeline()
    p.run()
