"""
Core python script for Money Man Spiff's arbitrage program

Uses the Kraken Exchange API to get data, and the Graph class to detect negative cycles

Author: Parker Timmerman
"""

from binance.client import Client as BinanceClient
from constants import Exchange
from decimal import *
from engine import ArbitrageEngine
from functools import partial
from graph import Graph, Edge
from math import log
from requests.exceptions import HTTPError
from time import sleep, time

import krakenex
import pprint
import ccxt

# A map of the ticker names on Kraken to the traditional ticker names
# make sure this includes all currencies from currencies.txt
KRAKEN_MAP = {
    'BTC': 'XBT',
    'BCH': 'BCH',
    'ETH': 'ETH',
    'LTC': 'LTC',
    'USDT': 'USD',
    'EOS': 'EOS',
    'XRP': 'XRP',
    'ZEC': 'ZEC',
    'GNO': 'GNO',
}

DELM = '/'

# Convinence Functions
def splitPair(currencies, pair) -> (str, str):
    """ Given a list of currencies, splits a given pair """
    for currency in currencies:
        if pair.startswith(currency):
            return (pair[:len(currency)], pair[len(currency):])

def containsTwo(currencies, pair):
    """ Used to filter whether or not a currency pair contains two currencies from the given list"""
    for i in range(len(currencies)):
        for j in range(i + 1, len(currencies)):
            if currencies[i] in pair and currencies[j] in pair:
                return True
    return False

class Pipeline():

    def __init__(self):
        """ Read in data, initialize the graph, open a connection to the API, and build Ticker string for querying to the API """
        self.CURRENCIES = [c.rstrip('\n') for c in open('currencies.txt').read().split(',')]
        self.G = Graph()
        cT = partial(containsTwo, self.CURRENCIES)
        
        # xSymbols is a list of strings that can be sent to an API to get order book info

        # Kraken
        kCURRENCIES = list(map(KRAKEN_MAP.get, self.CURRENCIES))    # List of supported currencies, mapped to Kraken symbols
        cTKraken = partial(containsTwo, kCURRENCIES)
        self.K = ccxt.kraken()
        kInfo = self.K.publicGetAssetPairs()['result']
        kRawPairs = [kInfo[pair]['altname'] for pair in kInfo]
        self.krakenSymbols = list(filter(cTKraken, kRawPairs))
        self.krakenSymbols = list(filter(lambda x: '.d' not in x, self.krakenSymbols))
        
        # Binance
        (bPublic, bSecret) = [line.rstrip('\n') for line in open('binance.key').readlines()]
        self.B = ccxt.binance()
        bInfo = self.B.publicGetExchangeInfo()
        bRawPairs = [entry['symbol'] for entry in bInfo['symbols']]
        self.binanceSymbols = list(filter(cT, bRawPairs))

        # Coinbase
        self.C = ccxt.coinbasepro()
        cInfo = self.C.publicGetProducts()
        cRawPairs = [entry['id'].replace('-', '') for entry in cInfo]
        self.coinbaseSymbols = list(filter(cT, cRawPairs))

        # Bitfinex
        self.bitfinex = ccxt.bitfinex()
        bitfinexInfo = self.bitfinex.publicGetSymbolsDetails()
        bitfinexRawPairs = [entry['pair'].upper() for entry in bitfinexInfo]
        self.bitfinexSymbols = list(filter(cT, bitfinexRawPairs))

        # Huobi
        self.huobi = ccxt.huobipro()
        huobiInfo = self.huobi.publicGetCommonSymbols()['data']
        huobiRawPairs = [entry['symbol'].upper() for entry in huobiInfo]
        self.huobiSymbols = list(filter(cT, huobiRawPairs))

        # Bitstamp
        self.bitstamp = ccxt.bitstamp()
        bitstampInfo = self.bitstamp.publicGetTradingPairsInfo()
        bitstampRawPairs = [entry['name'].replace('/', '') for entry in bitstampInfo]
        self.bitstampSymbols = list(filter(cT, bitstampRawPairs))

        self.E = ArbitrageEngine()
        getcontext().prec = 6                   # Set Decimal precision to 6 place
        getcontext().traps[FloatOperation] = True

    def initGraph(self):
        """ Initialize the graph's nodes, and edges. Set all edge values to 0 """
        # Initialize graph with nodes
        for currency in self.CURRENCIES:
            self.G.addNode(currency)

    def getTickerData(self, requestData):
        """ Given a comma seperated list of pairs, get the ticker information from the API 

            requestData should be formated as a list of tuples.
            1. Exhange Enum
            2. List of pairs to get from that exchange
        
            Returns a dict in the following format
            {
                'time': current UNIX time,
                'kraken': {
                    ('BCH', 'USDT'): {
                        'ask': ###
                        'bid': ###
                        'ask_vol': ###
                        'bid_vol': ###
                    }
                    ...
                },
                'binance': {
                    ... same as above
                },
            }
        """

        # Kraken names its pairs very weirdly, so map the weird pair names to the more common names
        KRAKEN_PAIRS_MAP = {
            'BCHUSD': ('BCH', 'USDT'), 'BCHXBT': ('BCH', 'BTC'), 'EOSETH': ('EOS', 'ETH'),
            'EOSUSD': ('EOS', 'USDT'), 'EOSXBT': ('EOS', 'BTC'), 'XETHXXBT': ('ETH', 'BTC'),
            'XETHZUSD': ('ETH', 'USDT'), 'XLTCXXBT': ('LTC', 'BTC'), 'XLTCZUSD': ('LTC', 'USDT'),
            'XXBTZUSD': ('BTC', 'USDT'), 'XXRPXXBT': ('XRP', 'USDT'), 'XXRPZUSD': ('XRP', 'USDT'),
            'GNOETH': ('GNO', 'ETH'), 'GNOUSD': ('GNO', 'USDT'), 'GNOXBT': ('GNO', 'BTC'),
            'XZECXXBT': ('ZEC', 'USDT'), 'XZECZUSD': ('ZEC', 'USDT')
        }
        timestamp = int(time())  # Stamp each request with the local time which we requested it

        retVal = {'time': timestamp}

        for request in requestData:
            if request[0] is Exchange.KRAKEN:
                # Query kraken for data about our pairs
                resp = self.K.publicGetTicker({'pair': ','.join(request[1])})
                if not resp['error'] == []:
                    pprint.pprint(resp['error'])
                else:
                    kResp = resp['result']

                krakenResp = {}
                # Given data for all of our pairs, format them in a way we can easily handle
                for resp in kResp:
                    data = kResp[resp]
                    krakenResp[KRAKEN_PAIRS_MAP[resp]] =  {
                            'ask': data['a'][0],
                            'bid': data['b'][0],
                            'ask_vol': data['a'][2],
                            'bid_vol': data['b'][2],
                    }
                retVal[Exchange.KRAKEN] = krakenResp
                
            if request[0] is Exchange.BINANCE:
                # Query binance for data about our pairs
                sP = partial(splitPair, self.CURRENCIES)
                binanceResp = {}
                for sym in self.binanceSymbols:
                    resp = self.B.publicGetDepth({'symbol': sym, 'limit': 5})   # Get order book for symbol at depth of 5
                    binanceResp[sP(sym)] = {
                            'ask': resp['asks'][0][0],
                            'bid': resp['bids'][0][0],
                            'ask_vol': resp['asks'][0][1],
                            'bid_vol': resp['bids'][0][1],
                    }
                retVal[Exchange.BINANCE] = binanceResp

            if request[0] is Exchange.COINBASE:
                sP = partial(splitPair, self.CURRENCIES)
                pairs = [sP(pair) for pair in self.coinbaseSymbols]
                coinbaseResp = {}
                for pair in pairs:
                    resp = self.C.fetch_order_book(pair[0] + '/' + pair[1])
                    coinbaseResp[pair] = {
                        'ask': resp['asks'][0][0],
                        'bid': resp['bids'][0][0],
                        'ask_vol': resp['asks'][0][1],
                        'bid_vol': resp['bids'][0][1]
                    }
                retVal[Exchange.COINBASE] = coinbaseResp

            if request[0] is Exchange.BITFINEX:
                sP = partial(splitPair, self.CURRENCIES)
                pairs = [sP(pair) for pair in self.bitfinexSymbols]
                bitfinexResp = {}
                for pair in pairs:
                    resp = self.bitfinex.fetch_order_book(pair[0] + '/' + pair[1])
                    bitfinexResp[pair] = {
                        'ask': resp['asks'][0][0],
                        'bid': resp['bids'][0][0],
                        'ask_vol': resp['asks'][0][1],
                        'bid_vol': resp['bids'][0][1]
                    }
                retVal[Exchange.BITFINEX] = bitfinexResp

            if request[0] is Exchange.HUOBI:
                sP = partial(splitPair, self.CURRENCIES)
                pairs = [sP(pair) for pair in self.huobiSymbols]
                huobiResp = {}
                for pair in pairs:
                    resp = self.huobi.fetch_order_book(pair[0] + '/' + pair[1])
                    huobiResp[pair] = {
                        'ask': resp['asks'][0][0],
                        'bid': resp['bids'][0][0],
                        'ask_vol': resp['asks'][0][1],
                        'bid_vol': resp['bids'][0][1]
                    }
                retVal[Exchange.HUOBI] = huobiResp

            if request[0] is Exchange.BITSTAMP:
                sP = partial(splitPair, self.CURRENCIES)
                pairs = [sP(pair) for pair in self.bitstampSymbols]
                bitstampResp = {}
                for pair in pairs:
                    resp = self.bitstamp.fetch_order_book(pair[0] + '/' + pair[1])
                    bitstampResp[pair] = {
                        'ask': resp['asks'][0][0],
                        'bid': resp['bids'][0][0],
                        'ask_vol': resp['asks'][0][1],
                        'bid_vol': resp['bids'][0][1]
                    }
                retVal[Exchange.BITSTAMP] = bitstampResp

        return retVal

    def updateGraph(self, data):
        """ Given data from the API update the edge weights of the graph """
        timestamp = data['time']
        kraken = data[Exchange.KRAKEN]
        binance = data[Exchange.BINANCE]
        coinbase = data[Exchange.COINBASE]
        bitfinex = data[Exchange.BITFINEX]
        huobi = data[Exchange.HUOBI]
        bitstamp = data[Exchange.BITSTAMP]

        for orderBook in kraken.items():
            pair = orderBook[0]
            ask = float(orderBook[1]['ask'])
            bid = float(orderBook[1]['bid'])
            ask_vol = float(orderBook[1]['ask_vol'])
            bid_vol = float(orderBook[1]['bid_vol'])

            w1 = -(log(bid, 2))
            w2 = -(log((1/ask), 2))

            self.G.addEdge(pair[0], pair[1], bid, w1, bid_vol, pair[0], pair, 'bid', Exchange.KRAKEN, timestamp)
            self.G.addEdge(pair[1], pair[0], 1/ask, w2, ask_vol, pair[0], pair, 'ask', Exchange.KRAKEN, timestamp)
            
        for orderBook in binance.items():
            pair = orderBook[0]
            ask = float(orderBook[1]['ask'])
            bid = float(orderBook[1]['bid'])
            ask_vol = float(orderBook[1]['ask_vol'])
            bid_vol = float(orderBook[1]['bid_vol'])

            w1 = -(log(bid, 2))
            w2 = -(log((1/ask), 2))

            self.G.addEdge(pair[0], pair[1], bid, w1, bid_vol, pair[0], pair, 'bid', Exchange.BINANCE, timestamp)
            self.G.addEdge(pair[1], pair[0], 1/ask, w2, ask_vol, pair[0], pair, 'ask', Exchange.BINANCE, timestamp)

        for orderBook in coinbase.items():
            pair = orderBook[0]
            ask = float(orderBook[1]['ask'])
            bid = float(orderBook[1]['bid'])
            ask_vol = float(orderBook[1]['ask_vol'])
            bid_vol = float(orderBook[1]['bid_vol'])

            w1 = -(log(bid, 2))
            w2 = -(log((1/ask), 2))

            self.G.addEdge(pair[0], pair[1], bid, w1, bid_vol, pair[0], pair, 'bid', Exchange.COINBASE, timestamp)
            self.G.addEdge(pair[1], pair[0], 1/ask, w2, ask_vol, pair[0], pair, 'ask', Exchange.COINBASE, timestamp)

        for orderBook in bitfinex.items():
            pair = orderBook[0]
            ask = float(orderBook[1]['ask'])
            bid = float(orderBook[1]['bid'])
            ask_vol = float(orderBook[1]['ask_vol'])
            bid_vol = float(orderBook[1]['bid_vol'])

            w1 = -(log(bid, 2))
            w2 = -(log((1/ask), 2))

            self.G.addEdge(pair[0], pair[1], bid, w1, bid_vol, pair[0], pair, 'bid', Exchange.BITFINEX, timestamp)
            self.G.addEdge(pair[1], pair[0], 1/ask, w2, ask_vol, pair[0], pair, 'ask', Exchange.BITFINEX, timestamp)

        for orderBook in huobi.items():
            pair = orderBook[0]
            ask = float(orderBook[1]['ask'])
            bid = float(orderBook[1]['bid'])
            ask_vol = float(orderBook[1]['ask_vol'])
            bid_vol = float(orderBook[1]['bid_vol'])

            w1 = -(log(bid, 2))
            w2 = -(log((1/ask), 2))

            self.G.addEdge(pair[0], pair[1], bid, w1, bid_vol, pair[0], pair, 'bid', Exchange.HUOBI, timestamp)
            self.G.addEdge(pair[1], pair[0], 1/ask, w2, ask_vol, pair[0], pair, 'ask', Exchange.HUOBI, timestamp)

        for orderBook in bitstamp.items():
            pair = orderBook[0]
            ask = float(orderBook[1]['ask'])
            bid = float(orderBook[1]['bid'])
            ask_vol = float(orderBook[1]['ask_vol'])
            bid_vol = float(orderBook[1]['bid_vol'])

            w1 = -(log(bid, 2))
            w2 = -(log((1/ask), 2))

            self.G.addEdge(pair[0], pair[1], bid, w1, bid_vol, pair[0], pair, 'bid', Exchange.BITSTAMP, timestamp)
            self.G.addEdge(pair[1], pair[0], 1/ask, w2, ask_vol, pair[0], pair, 'ask', Exchange.BITSTAMP, timestamp)

    def checkArbitrage(self, path):
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
            edge = self.G.getEdge(a, b)

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
        # Initialize graph
        self.initGraph()
        
        while True:
            try:
                data = self.getTickerData([
                    (Exchange.KRAKEN, self.krakenSymbols),
                    (Exchange.BINANCE, self.binanceSymbols),
                    (Exchange.COINBASE, self.coinbaseSymbols),
                    (Exchange.BITFINEX, self.bitfinexSymbols),
                    (Exchange.HUOBI, self.huobiSymbols),
                    (Exchange.BITSTAMP, self.bitstampSymbols)
                ])
                self.updateGraph(data)
                self.G.print()
                path = self.G.BellmanFord('BTC')
                if path:
                    self.checkArbitrage(path)
                    self.E.exploitArbitrage(self.G, path)
                sleep(10)
            except Exception as e:
                pprint.pprint(e)
                sleep(120)
            
        #self.G.print()

if __name__ == '__main__':
    p = Pipeline()
    p.run()
