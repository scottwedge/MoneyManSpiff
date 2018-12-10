from collections import namedtuple

class ValuePair(object):
    def __init__(
        self,
        amt,
        amt_usd
    ):
        self.amt = amt
        self.amt_usd = amt_usd

    def __repr__(self):
        return "Amount: {0} Amount USD: {1}".format(self.amt, self.amt_usd)

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
        self.buyOrSell = buyOrSell      # type: BS
        self.orderType = orderType      # type: OrderType
        self.pair = pair                # type: (Currency, Currency)
        self.price = price              # type: float
        self.volume = volume            # type: float

    def toStringShort(self):
        return "{0} {1} of {2} on {3} @ {4}".format(self.buyOrSell, self.volume, self.pair, self.exchange, self.price)

    def __repr__(self):
        return "Order:\n\tExchange: {0}\n\t{1}\n\t{2}\n\t{3}\n\tPrice: {4}\n\t{5}\n".format(
            self.exchange,
            self.buyOrSell,
            self.orderType,
            self.pair,
            self.price,
            self.volume,
        )

class ApiError(Exception):
    """ Class to represent an API Error """
    pass
    
