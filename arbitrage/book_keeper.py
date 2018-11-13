"""
Global singleton object that keeps an offline representation of our current assets, and open trades.

Author: Parker Timmerman
"""
from constants import Currency, Exchange, OrderType
from market_engine import MarketEngine
from my_types import Order, ValuePair

class BookKeeper():
    class _BookKeeper():
        def __init__(self):
            """
            Example of positions:
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
            self._positions = {}
            self._trades = []

            self.count = 0

        def sayHello(self):
            """ Sanity check method to make sure the singleton works as it should """

            print('Hello I\'m the Book Keeper, I\'ve said hi {} times'.format(self.count))
            self.count += 1

        def addExchange(self, exch: Exchange) -> None:
            if exch in self._positions:
                raise TypeError('Exchange already exists in the positions map, check what you\'re doing')
            else:
                self._positions[exch] = {}

        def addCurrencyToExchange(self, exch: Exchange, curr: Currency, value_pair: ValuePair = ValuePair(0,0)) -> None:
            """
            Given an exchange, and a currency, will add that currency value under the given exchange, with an initial value
            pair of (0, 0). Value pair can be override with the argument 'value_pair'
            """
            if not exch in self._positions:
                raise TypeError('Exchange is not in the positions map, please add it before trying to add a currency to it')
            else:
                if curr in self._positions[exch]:
                    raise TypeError('Currency is already in this exchange, please use the updateCurrencyInExchange(...) method')
                else:
                    self._positions[exch][curr] = value_pair

        def updateCurrencyInExchange(self, exch: Exchange, curr: Currency, value_pair: ValuePair) -> None:
            """
            Given an exchange, a currency, and a value pair, will update the amount of currency we have in that exchange
            with the given value pair.
            """
            if not exch in self._positions:
                raise TypeError('Exchange is not in the positions map, please add it before trying to add a currency to it')
            else:
                if not curr in self._positions[exch]:
                    raise TypeError('Currency is not in the positions map for this exchange, please add it before trying to update it')
                else:
                    self._positions[exch][curr] = value_pair

        def updatePosition(self, exch: Exchange, position: {}) -> None:
            """
            Given an exchange, and a map for that exchange of Currency -> ValuePair, updates our positions
            Example
            exch = Exchange.BINANCE
            position = {
                Currency.BTC: (10, 20),
                Currency.ETH: (100, 100),
            }
            """
            if not exch in self._positions:
                raise TypeError('Exchange is not in the positions map, please add it before trying to add a currency to it')
            for key in position.keys():
                self.updateCurrencyInExchange(exch=exch, curr=key, value_pair=position[key])

        def getValuePairOfCurrencyInExchange(self, exch: Exchange, curr: Currency) -> ValuePair:
            """
            Given an exchange and a currency returns the value pair for that currency.
            """
            if not exch in self._positions:
                raise TypeError('Exchange is not in the positions map, please add it before trying to get a value from it')
            else:
                if not curr in self._positions[exch]:
                    raise TypeError('Currency is not in the positions map for this exchange, please add it before trying to get its value pair')
                else:
                    return self._positions[exch][curr]

        def getPositions(self):
            """
            Returns the positions map
            """
            return self._positions

        def addOrder(self, trade: Order):
            self._trades.append(trade)

        def clear(self):
            """ DANGEROUS! Clears out the singleton object, losing all records. Primarily used for testing """
            self._positions = {}
            self._trades = []

        def sync(self):
            """
            Will make a network request to check current positions as the are held in the various exchanges in the positions map
            Then updates the positions map to reflect our positions, logging any differences.

            Note: This results in several network requests, so DO NOT call it with the intention of it being fast.
                  Preferablly call it when trading is paused.
            """
            exchanges = MarketEngine.instance().supportedExchanges()
            for exchange in exchanges:
                position = MarketEngine.instance().fetchBalance(exchange)
                self.updatePosition(
                    exch=exchange,
                    position=position,
                )





    INSTANCE = None
    @classmethod
    def instance(cls):
        """
        Returns the singleton instance. On its first call, raises and error and then calls the
        classes constructor to create an instance.
        """
        if BookKeeper.INSTANCE:
            return BookKeeper.INSTANCE
        else:
            BookKeeper.INSTANCE = cls._BookKeeper()
            return BookKeeper.INSTANCE

    def __call__(self):
        raise TypeError('BookKeeper must be accessed through \'BookKeeper.instance()\'.')