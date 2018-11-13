from collections import namedtuple

class ValuePair(object):
    def __init__(
        self,
        amt,
        amt_usd
    ):
        self.amt = amt
        self.amt_usd = amt_usd

class Order(object):
    def __init__(
        self,
        exchange,
        buyOrSell,
        orderType,
        pair,
        price,
        volume
    ):
        self.exchange = exchange        # type: Exchange
        self.buyOrSell = buyOrSell      # type: BuyOrSell
        self.orderType = orderType      # type: OrderType
        self.pair = pair                # type: String
        self.price = price              # type: float
        self.volume = volume            # type: float

class ApiError(Exception):
    """ Class to represent an API Error """
    pass
    
