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

class BS(Enum):
    BUY = 'BUY'
    SELL = 'SELL'

class OrderType(Enum):
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'

class SafetyValues(Enum):
    """
    Contants for our safety standards. All values are in USD
    """
    MinimumLiquidAssetsUSD = 200
    MaximumOrderValueUSD = 12
    MinimumOrderValueUSD = 5
    MaximumOpenTrades = 1
    MinimumOpportunity = 0.9                # This value is in percent i.e. 0.5%

class TimeUnit(Enum):
    Milliseconds = 'milliseconds'
    Seconds = 'seconds'

# Kraken uses some weird symbols, below are maps from normal -> kraken and vice versa
# This is a map of normal (n) -> (TO) kraken (k) symbols
nTOk = {
    'BTC': 'XXBT',
    'BCH': 'XBCH',
    'ETH': 'XETH',
    'LTC': 'XLTC',
    'USDT': 'ZUSD',
    'EOS': 'XEOS',
    'XRP': 'XXRP',
    'ZEC': 'XZEC',
    'GNO': 'XGNO',
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

# Map of exchange to exchange fees
# (Maker, Taker)
feeMap = {
    Exchange.KRAKEN: (0.0016, 0.0026),
    Exchange.BINANCE: (0.001, 0.001),
}
