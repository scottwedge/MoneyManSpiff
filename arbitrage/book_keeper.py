"""
Global singleton object that keeps an offline representation of our current assets, and open trades.

Author: Parker Timmerman
"""
from typing import List

from constants import BS, Currency, Exchange, OrderType
from my_types import Order, ValuePair
from virtual_market import VirtualMarket

class BookKeeper():
    class _BookKeeper():
        def __init__(self, currencies, exchanges):
            """
            Example of balances:
            {
                Exchange.BINANCE: {
                    Currency.BTC: (0.2, $1,267),
                    Currency.ETH: (0.1), $501),
                },
                Exchange.KRAKEN: {
                    Currency.BTC: (0.5, $3,000),
                    Currency.ETH: (0.2, $1002),
                },
            }
            """
            self._balances = {}
            self._trades = []

            self._supportedExchanges = exchanges
            self._supportedCurrencies = currencies

            for exchange in self._supportedExchanges:
                self.addExchange(exchange)
                for currency in self._supportedCurrencies:
                    self.addCurrencyToExchange(exchange, currency)

            self.count = 0

        def sayHello(self):
            """ Sanity check method to make sure the singleton works as it should """

            print('Hello I\'m the Book Keeper, I\'ve said hi {} times'.format(self.count))
            self.count += 1

        def addExchange(self, exch: Exchange) -> None:
            if exch in self._balances:
                raise TypeError('Exchange already exists in the balances map, check what you\'re doing')
            else:
                self._balances[exch] = {}

        def addCurrencyToExchange(self, exch: Exchange, curr: Currency, value_pair: ValuePair = ValuePair(0,0)) -> None:
            """
            Given an exchange, and a currency, will add that currency value under the given exchange, with an initial value
            pair of (0, 0). Value pair can be override with the argument 'value_pair'
            """
            if not exch in self._balances:
                raise TypeError('Exchange is not in the balances map, please add it before trying to add a currency to it')
            else:
                if curr in self._balances[exch]:
                    raise TypeError('Currency is already in this exchange, please use the updateCurrencyInExchange(...) method')
                else:
                    self._balances[exch][curr] = value_pair

        def updateCurrencyInExchange(self, exch: Exchange, curr: Currency, value_pair: ValuePair) -> None:
            """
            Given an exchange, a currency, and a value pair, will update the amount of currency we have in that exchange
            with the given value pair.
            """
            if not exch in self._balances:
                raise TypeError('Exchange is not in the balances map, please add it before trying to add a currency to it')
            else:
                if not curr in self._balances[exch]:
                    raise TypeError('Currency is not in the balances map for this exchange, please add it before trying to update it')
                else:
                    self._balances[exch][curr] = value_pair

        def reportOrder(self, order=Order):
            """
            Given an order, updates the positions for that exchange
            """
            exch = order.exchange
            if not exch in self._balances:
                raise TypeError('Exchange is not in the balances map, please add it before trying to add a currency to it')
            
            acq_curr = order.pair[0]
            acq_amt = order.volume

            los_curr = order.pair[1]
            los_amt = order.volume * order.price

            if order.buyOrSell == BS.SELL:
                acq_amt = acq_amt * -1
            else:
                los_amt = los_amt * -1

            new_acq_amt = acq_amt + self._balances[exch][acq_curr].amt
            new_los_amt = los_amt + self._balances[exch][los_curr].amt

            new_acq_amt_usd = VirtualMarket.instance().convertCurrency(
                exch=order.exchange,
                amt=new_acq_amt,
                start=acq_curr,
                end=Currency.USDT,
            )
            self._balances[exch][acq_curr] = ValuePair(
                amt=new_acq_amt,
                amt_usd=new_acq_amt_usd,
            )

            new_los_amt_usd = VirtualMarket.instance().convertCurrency(
                exch=order.exchange,
                amt=new_los_amt,
                start=los_curr,
                end=Currency.USDT,
            )
            self._balances[exch][los_curr] = ValuePair(
                amt=new_los_amt,
                amt_usd=new_los_amt_usd,
            )


        def updateBalance(self, exch: Exchange, balance: {}) -> None:
            """
            Given an exchange, and a map for that exchange of Currency -> ValuePair, updates our balances
            Example
            exch = Exchange.BINANCE
            balance = {
                Currency.BTC: (10, 20),
                Currency.ETH: (100, 100),
            }
            """
            if not exch in self._balances:
                raise TypeError('Exchange is not in the balances map, please add it before trying to add a currency to it')
            for key in balance.keys():
                self.updateCurrencyInExchange(exch=exch, curr=key, value_pair=balance[key])

        def getValuePairOfCurrencyInExchange(self, exch: Exchange, curr: Currency) -> ValuePair:
            """
            Given an exchange and a currency returns the value pair for that currency.
            """
            if not exch in self._balances:
                raise TypeError('Exchange is not in the balances map, please add it before trying to get a value from it')
            else:
                if not curr in self._balances[exch]:
                    raise TypeError('Currency is not in the balances map for this exchange, please add it before trying to get its value pair')
                else:
                    return self._balances[exch][curr]

        def getMaxOrderVolumeOfCurrency(self, curr: Currency) -> float:
            """
            Given a currency, returns the max order volume that could
            be fullfilled by every exchange
            """
            max_volume = 1000000000
            for exchange in self._balances.keys():
                max_volume = min(max_volume, self._balances[exchange][curr])
            return max_volume

        def getMaxOrdersVolume(self, orders: List[Order]) -> float:
            """
            Given a list of orders, determines max trade size we can make to fullfill all orders.

            For each order, determines the currency needed to fullfil the order. Then checks
            the given exchange for how much of that currency we have.
            """
            volumes = []
            for order in orders:
                required_currency = order.pair[0] if order.buyOrSell is BS.SELL else order.pair[1]
                

        def getPositions(self):
            """
            Returns the balances map
            """
            return self._balances

        def addOrder(self, trade: Order):
            self._trades.append(trade)

        def clear(self):
            """ DANGEROUS! Clears out the singleton object, losing all records. Primarily used for testing """
            self._balances = {}
            self._trades = []

    INSTANCE = None
    @classmethod
    def initialize(cls, currencies, exchanges):
        BookKeeper.INSTANCE = cls._BookKeeper(currencies, exchanges)


    @classmethod
    def instance(cls):
        """
        Returns the singleton instance. On its first call, raises and error and then calls the
        classes constructor to create an instance.
        """
        if BookKeeper.INSTANCE:
            return BookKeeper.INSTANCE
        else:
            raise AttributeError('You must initialize the BookKeeper before trying to use it!')

    def __call__(self):
        raise TypeError('BookKeeper must be accessed through \'BookKeeper.instance()\'.')