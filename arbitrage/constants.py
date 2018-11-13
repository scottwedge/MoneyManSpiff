from enum import Enum

class Exchange(Enum):
    BINANCE = 'binance'     # Japan ?
    COINBASE = 'coinbase'   # California, USA
    KRAKEN = 'kraken'       # California, USA
    BITFINEX = 'bitfinex'   # Hong Kong / British Virgin Islands
    HUOBI = 'huobi'         # China
    BITSTAMP = 'bitstamp'   # UK

class Currency(Enum):
    BTC = 'BTC'             # Bitcoin
    BCH = 'BCH'             # Bitcoin Cash
    ETH = 'ETH'             # Ethereum
    LTC = 'LTC'             # Litecoin
    USDT = 'USDT'           # US Dollar Tether
    EOS = 'EOS'             # EOS
    XRP = 'XRP'             # Ripple
    ZEC = 'ZEC'             # Z-Cash
    GNO = 'GNO'             # Gnosis

class CurrencyPair(Enum):
    XRPUSDT = (Currency.XRP, Currency.USDT)
    EOSUSDT = (Currency.EOS, Currency.USDT)

class BuyOrSell(Enum):
    BUY = 'buy'
    SELL = 'sell'

class OrderType(Enum):
    MARKET = 'market'
    LIMIT = 'limit'

class SafetyValues(Enum):
    """
    Contants for our safety standards. All values are in USD
    """
    MinimumLiquidAssets = 100
    MaximumOrderValue = 20
    MaximumOpenTrades = 1

class TimeUnit(Enum):
    Milliseconds = 'milliseconds'
    Seconds = 'seconds'

# Kraken uses some weird symbols, below are maps from normal -> kraken and vice versa
# This is a map of normal (n) -> (TO) kraken (k) symbols
nTOk = {
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
# This is a map of kraken (k) -> (TO) normal (n) symbols
kTOn = {
    'XXBT': 'BTC',
    'XBCH': 'BCH',
    'XETH': 'ETH',
    'XLTC': 'LTC',
    'ZUSD': 'USDT',
    'XEOS': 'EOS',
    'XXRP': 'XRP',
    'XZEC': 'ZEC',
    'XGNO': 'GNO',
}

