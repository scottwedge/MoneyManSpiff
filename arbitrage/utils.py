from constants import TimeUnit
from functools import partial
from math import floor
from time import time

def timestamp(unit: TimeUnit = TimeUnit.Seconds):
    """ 
    Helper utility function to get the timestamp in either seconds or milliseconds
        @param unit: TimeUnit = TimeUnit.Seconds
    """
    ts = time() if unit is TimeUnit.Seconds else time() * 1000
    return floor(ts)

def loadKeys(path):
    """ Helper method to load API keys from file """
    with open(path) as fs:
        content = fs.readlines()
    (public, secret) = [line.rstrip('\n') for line in content]
    return (public, secret)

# Partial functions to make loading keys easier
loadKrakenKeys = partial(loadKeys, 'keys/kraken.key')
loadBinanceKeys = partial(loadKeys, 'keys/binance.key')

def validPair(currencies, pair):
    """
    Given a list of currencies we support trading on, determins if the pair is valid
    """
    for i in range(len(currencies)):
        for j in range(i + 1, len(currencies)):
            if currencies[i] in pair and currencies[j] in pair:
                return True
    return False
