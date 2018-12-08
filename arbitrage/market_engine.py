"""
Singleton object used to make trades and query the exchanges for information

Author: Parker Timmerman
"""
import ccxt

from book_keeper import BookKeeper
from constants import (
    Currency,
    Exchange,
    kTOn,
    nTOk,
    SafetyValues,
    TimeUnit
)
from functools import partial
from utils import loadKrakenKeys, loadBinanceKeys, timestamp, validPair
from my_types import ApiError, Order
from pprint import pprint
from time import time
from typing import List

class MarketEngine():
    class _MarketEngine():
        def __init__(self):
            krakenKeys = loadKrakenKeys()
            self._kraken = ccxt.kraken({
                'apiKey': krakenKeys[0],
                'secret': krakenKeys[1],
                'verbose': False,
            })

            binanceKeys = loadBinanceKeys()
            self._binance = ccxt.binance({
                'apiKey': binanceKeys[0],
                'secret': binanceKeys[1],
                'verbose': False,
            })

            self._supportedExchanges = [
                Exchange.BINANCE,
                Exchange.KRAKEN,
            ]

            # Load currencies from supported_currencies file
            with open('supported_currencies.txt') as fs:
                content = fs.read()
            self._supportedCurrencies = [Currency[c.rstrip('\n')] for c in content.split(',')]

            self._supportedCurrencyPairs = [
                (Currency.XRP, Currency.USDT),
                (Currency.EOS, Currency.USDT),
            ]

    # ======== Query for information ========
        
        # ======== Fetch Balances ========
        def _fetchKrakenBalance(self):
            """
            Makes an API POST request to the Kraken API instance asking for our account balances

            Example Response:
            {
                'error': [],
                'result': {
                    'XETH': '0.0998591200',
                }
            }
            """
            if not self._kraken:
                raise AttributeError('Kraken API instance has not been instanciated')
            resp = self._kraken.privatePostBalance()
            if resp['error']:
                raise ApiError('kraken api did not return a correct response')
            else:
                balances = resp['result']
                position = {}
                for (curr, amt) in balances.items():
                    # Note: need to convert to native currency
                    position[Currency[kTOn[curr]]] = (amt, amt)
                return position


        def _fetchBinanceBalance(self):
            """
            Makes an API POST request to the Binance API instance asking for our account balances

            Example response:
            {
                "makerCommission": 15,
                "takerCommission": 15,
                "buyerCommission": 0,
                "sellerCommission": 0,
                "canTrade": true,
                "canWithdraw": true,
                "canDeposit": true,
                "updateTime": 123456789,
                "balances": [
                    {
                      "asset": "BTC",
                      "free": "4723846.89208129",               <= USD?
                      "locked": "0.00000000"
                    },
                    {
                      "asset": "LTC",
                      "free": "4763368.68006011",               <= USD?
                      "locked": "0.00000000"
                    }
                ]
            }              
            """
            if not self._binance:
                raise AttributeError('Binance API instance has not been instanciated')
            resp = self._binance.privateGetAccount()        
            if not 'balances' in resp:
                raise ApiError('binance api did not return a correct response')
            else:
                balances = resp['balances']
                position = {}
                for entry in balances:
                    # Note: need to convert to native currency
                    position[Currency[entry['asset']]] = (entry['free'], entry['free'])
                return position

        def fetchBalance(self, exch: Exchange):
            """
            Public function to fetch the balance from one of the exchanges
            """
            if exch == Exchange.KRAKEN:
                return self._fetchKrakenBalance()
            if exch == Exchange.BINANCE:
                return self._fetchBinanceBalance()
            else:
                raise NotImplementedError('fetch balance not implemented for {}'.format(exch))

        def _fetchTickerKraken(self, first: Currency, second: Currency):
            """
            Private function to query kraken for ticker data for a pair of currencies
            """
            firstToK = nTOk[first.value]
            secondToK = nTOk[second.value]
            resp = self._kraken.publicGetTicker({'pair': '{0}{1}'.format(firstToK, secondToK)})
            if resp['error']:
                raise ApiError('kraken api returned an error:\n{}'.format(resp['error']))
            
            data = list(resp['result'].items())[0][1]
            return ((first, second), {
                'ask': float(data['a'][0]),
                'bid': float(data['b'][0]),
                'ask_vol': float(data['a'][2]),      # Kraken sometimes rounds up on its order volumes
                'bid_vol': float(data['b'][2]),      # i.e. 742.4 gets returned as 743.00
            })

        def _fetchTickerBinance(self, first: Currency, second: Currency):
            """
            Private function to query binance for ticker data for a pair of currencies
            """
            resp = self._binance.publicGetDepth({'symbol': '{0}{1}'.format(first.value, second.value), 'limit': 5})
            if not 'asks' in resp or not 'bids' in resp:
                raise ApiError('binance api returned an error:\n{}'.format(resp))
            return ((first, second), {
                'ask': float(resp['asks'][0][0]),
                'bid': float(resp['bids'][0][0]),
                'ask_vol': float(resp['asks'][0][1]),
                'bid_vol': float(resp['bids'][0][1]),
            })

        def fetchTicker(self, exch: Exchange, first: Currency, second: Currency):
            """
            Public function to query an exchange for ticker data for a pair of currencies

            Example return value:
            (
                (<Currency.XRP: 'XRP'>, <Currency.USDT: 'USDT'>),
                {'ask': 0.51003000, 'bid': 0.50960000, 'ask_vol': 195.000, 'bid_vol': 30.000}
            )

            return[0] = (<Currency.XRP: 'XRP'>, <Currency.USDT: 'USDT'>)
            return[1] = {'ask': 0.51003000, 'bid': 0.50960000, 'ask_vol': 195.000, 'bid_vol': 30.000}
            """
            if exch is Exchange.KRAKEN:
                return self._fetchTickerKraken(first=first, second=second)
            if exch is Exchange.BINANCE:
                return self._fetchTickerBinance(first=first, second=second)
            else:
                raise NotImplementedError('fetch ticker data not implemented for {}'.format(exch))

        def fetchTickers(self, exch: Exchange, pairs):
            """
            Public function to query an exchange for a list of pairs

            Example return value:
            {
                (<Currency.XRP: 'XRP'>, <Currency.USDT: 'USDT'>): {'ask': '0.51003000', 'bid': '0.50960000', 'ask_vol': '195.000', 'bid_vol': '30.000'},
                (<Currency.EOS: 'EOS'>, <Currency.USDT: 'USDT'>): {'ask': '0.51003000', 'bid': '0.50960000', 'ask_vol': '195.000', 'bid_vol': '30.000'}
            }

            NOTE: This is not optimal, if possible batch requests
            """
            data = {}
            for pair in pairs:
                if len(pair) != 2:
                    raise AttributeError('pair formatted incorrectly! {}'.format(pair))
                currencies, values = self.fetchTicker(
                    exch=exch,
                    first=pair[0],
                    second=pair[1]
                )
                data[currencies] = values
            return data

        
        # ======== Get Tradeable Pairs ========
        def _getTradeablePairsKraken(self):
            """
            Queries Kraken to get its tradeable pairs and filters that data down to just a list of pairs.
            Kraken has wierd names for their pairs (XBT v. BTC) so convert our support currencies to the 
            kraken names. Then find all the Kraken pairs that contain two of our supported currencies
            """
            if not self._kraken:
                raise AttributeError('Kraken API instance has not been instanciated')
            resp = self._kraken.publicGetAssetPairs()
            keyword = 'result'
            if not keyword in resp:
                raise ApiError('Kraken api did not return a valid response')
            assetPairInfo = resp[keyword]
            rawAssetPairs = [assetPairInfo[pair]['altname'] for pair in assetPairInfo]
            
            krakenFormattedSupportedCurrencies = list(map(nTOk.get, self.supportedCurrenciesString()))
            validKrakenPair = partial(validPair, krakenFormattedSupportedCurrencies)
            krakenPairs = list(filter(validKrakenPair, rawAssetPairs))
            return list(filter(lambda x: '.d' not in x, krakenPairs))
            



    # ======== Make Trades ========

        def _makeTradeKraken(self, order: Order):
            """
            Makes an API POST Request to the Kraken API to place an order
            Response Format:
            {
                descr = order description info: {
                    order = order description
                    close = conditional close order description (if conditional close set)
                },
                txid = array of transaction ids for order (if order was added successfully)
            }
            """
            if not self._kraken:
                raise AttributeError('Kraken API instance has not been initialized')
            return self._kraken.privatePostAddOrder({
                'pair': order.pair,
                'type': order.buyOrSell,
                'orderType': order.orderType,
                'price': order.price,
                'volume': order.volume,
            })

        def _makeTradeBinance(self, order: Order):
            """
            Makes an API POST Request to the Binance API to place an order

            Note: If Binance receives the order at a time > timestamp + 3000 then the order is invalid
            and it will not get posted.
            """
            if not self._binance:
                raise AttributeError('Binance API instance has not been initalized')
            return self._binance.privatePostOrder({
                'pair': order.pair,
                'type': order.orderType,
                'side': order.buyOrSell,
                'quantity': order.volume,
                'price': order.price,
                'recvWindow': 3000,
                'timestamp': str(timestamp(TimeUnit.Milliseconds))
            })

        def makeUnsafeTrade(self, order: Order, updateBookKeeper: bool = True):
            """
            Given an Order object, will post a trade to the market.
            WARNING: Ignores all safety standards and does not check BookKeeper for our current assets
            """
            if order.exchange is Exchange.KRAKEN:
                return self._makeTradeKraken(order)
            if order.exchange is Exchange.BINANCE:
                return self._makeTradeBinance(order)
            else:
                raise NotImplementedError('make trade is not implemented for {}'.format(order.exchange))

 #       def makeSafeTrades(self, orders: List[Order], sameVolume: bool = True, updateBookKeeper: bool = True):
 #           """
 #           Given a list of orders, will execute the orders such that they comply with our safety standards
#
 #           Note: For exploiting an arbitrage oppurtunity we need to make sure they all have the same
 #           volume, so the sameVolume flag defaults to True
 #           """
 #           currency = orders[0].pair[0]
 #           print(currency)
#
 #           cur_order_vol = orders[0].volume
 #           cur_order_vol_usd = ArbitrageEngine.instance().convertCurrency(
 #               amt=cur_order_vol,
 #               starting=currency, 
 #               ending=Currency.USDT
 #           )
#
 #           max_order_vol = BookKeeper.instance().getMaxOrderVolumeOfCurrency(currency)
 #           max_order_vol_usd = ArbitrageEngine.instance().convertCurrency(
 #               amt=max_order_vol,
 #               starting=currency,
 #               ending=Currency.USDT
 #           )
#
 #           order_volume_usd = min(SafetyValues.MaximumOrderValueUSD, max_order_vol_usd, cur_order_vol_usd)
#
 #           max_volume = min(SafetyValues.MaximumOrderValueUSD,


        def supportedExchanges(self) -> List[Exchange]:
            """
            Method that returns a list of exchanges supported by the Market Engine
            """
            return self._supportedExchanges

        def supportedCurrencies(self) -> List[Currency]:
            """
            Method that returns a list of currencies supported by the Market Engine
            """
            return self._supportedCurrencies
        def supportedCurrenciesString(self) -> List[str]:
            return list(map(lambda x: x.value, self._supportedCurrencies))

        def supportedCurrencyPairs(self):
            """
            Method that returns a list of currency pairs supported by the Market Engine
            """
            return self._supportedCurrencyPairs


    INSTANCE = None
    @classmethod
    def instance(cls):
        """
        Returns the singleton instance. On its first call, raises and error and then calls the
        classes constructor to create an instance.
        """
        if MarketEngine.INSTANCE:
            return MarketEngine.INSTANCE
        else:
            MarketEngine.INSTANCE = cls._MarketEngine()
            return MarketEngine.INSTANCE

    def __call__(self):
        raise TypeError('MarketEngine must be accessed through \'MarketEngine.instance()\'.')