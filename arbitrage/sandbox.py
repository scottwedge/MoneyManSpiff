from binance.client import Client as BinanceClient
from functools import partial
from time import time

import krakenex
import ccxt

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

# Convinence Functions
def splitPair(currencies, pair) -> (str, str):
    """ Given a list of currencies, splits a given pair """
    for currency in currencies:
        if pair.startswith(currency):
            return (pair[:len(currency)], pair[len(currency):])

def containsTwo(currencies, pair):
    for i in range(len(currencies)):
        for j in range(i + 1, len(currencies)):
            if currencies[i] in pair and currencies[j] in pair:
                return True
    return False

CURRENCIES = [c.rstrip('\n') for c in open('currencies.txt').read().split(',')]
cT = partial(containsTwo, CURRENCIES)

(bPublic, bSecret) = [line.rstrip('\n') for line in open('binance.key').readlines()]
B = ccxt.binance()
bInfo = B.publicGetExchangeInfo()
bRawPairs = [entry['symbol'] for entry in bInfo['symbols']]
bTradeablePairs = list(filter(cT ,bRawPairs))
print(bTradeablePairs)

sP = partial(splitPair, CURRENCIES)
bPairs = list(map(sP, bTradeablePairs))
print(bPairs)

cTKraken = partial(containsTwo, list(map(KRAKEN_MAP.get, CURRENCIES)))
K = ccxt.kraken()
kInfo = K.publicGetAssetPairs()['result']
kRawPairs = [kInfo[entry]['altname'] for entry in kInfo]
kTradeablePairs = list(filter(cTKraken, kRawPairs))
kTradeablePairs = list(filter(lambda x: '.d' not in x, kTradeablePairs))
print(kTradeablePairs)

sPKraken = partial(splitPair, list(map(KRAKEN_MAP.get, CURRENCIES)))
kPairs = list(map(sPKraken, kTradeablePairs))
print(kPairs)

# Coinbase
C = ccxt.coinbasepro()
cInfo = C.publicGetProducts()
cRawPairs = [entry['id'].replace('-', '') for entry in cInfo]
cTradeablePairs = list(filter(cT, cRawPairs))
print(cTradeablePairs)

cPairs = list(map(sP, cTradeablePairs))
print(cPairs)

# Bitfinex
bitfinex = ccxt.bitfinex()
bitfinexInfo = bitfinex.publicGetSymbolsDetails()
bitfinexRawPairs = [entry['pair'].upper() for entry in bitfinexInfo]
bitfinexTradeablePairs = list(filter(cT, bitfinexRawPairs))
print(bitfinexTradeablePairs)

# Huobi
huobi = ccxt.huobipro()
huobiInfo = huobi.publicGetCommonSymbols()['data']
huobiRawPairs = [entry['symbol'].upper() for entry in huobiInfo]
huobiTradeablePairs = list(filter(cT, huobiRawPairs))
print(huobiTradeablePairs)

# Bitstamp
bitstamp = ccxt.bitstamp()
bitstampInfo = bitstamp.publicGetTradingPairsInfo()
bitstampRawPairs = [entry['name'].replace('/', '') for entry in bitstampInfo]
bitstampSymbols = list(filter(cT, bitstampRawPairs))
print('Bitstamp')
print(bitstampSymbols)


for (a1, a2) in kPairs:
    print(a1 + ' : ' + a2)

print('Binance Time: ' + str(B.publicGetTime()['serverTime']))
print('Kraken Time: ' + str(K.publicGetTime()['result']['unixtime']))
print('Local Time: ' + str(time()))

kResp = K.publicGetTicker({'pair': ','.join(kTradeablePairs)})
for resp in kResp['result']:
    print(resp) 

for pair in bTradeablePairs:
    print(pair)
    print(B.publicGetDepth({'symbol': pair, 'limit': 5}))