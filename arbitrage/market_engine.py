"""
Singleton object used to make trades and query the exchanges for information

Author: Parker Timmerman
"""
import ccxt

from book_keeper import BookKeeper
from constants import (
    BS,
    Currency,
    Exchange,
    kTOn,
    nTOk,
    SafetyValues,
    TimeUnit
)
from functools import partial
from utils import loadKrakenKeys, loadBinanceKeys, timestamp, validPair
from my_types import ApiError, Order, ValuePair
from pprint import pprint
from time import time
from typing import List
from virtual_market import VirtualMarket

class MarketEngine():
    class _MarketEngine():
        def __init__(self):
            krakenKeys = loadKrakenKeys()
            self._kraken = ccxt.kraken({
                'apiKey': krakenKeys[0],
                'secret': krakenKeys[1],
                'verbose': False,
            })
            self._kraken.load_markets()

            binanceKeys = loadBinanceKeys()
            self._binance = ccxt.binance({
                'apiKey': binanceKeys[0],
                'secret': binanceKeys[1],
                'verbose': False,
            })
            self._binance.load_markets()

            self._supportedExchanges = [
                Exchange.BINANCE,
                Exchange.KRAKEN,
            ]

            # Load currencies from supported_currencies file
            with open('supported_currencies.txt') as fs:
                content = fs.read()
            self._supportedCurrencies = [Currency[c.rstrip('\n')] for c in content.split(',')]

            #(Currency.XRP, Currency.USDT),
            self._supportedCurrencyPairs = [
                (Currency.ETH, Currency.USDT),
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
                supported_currencies_string = list(map(lambda x: nTOk[x.value], self._supportedCurrencies))
                for (curr, amt) in balances.items():
                    if curr in supported_currencies_string:
                        currency = Currency[kTOn[curr]]
                        amount = float(amt)
                        usd_amount = VirtualMarket.instance().convertCurrency(
                            exch=Exchange.KRAKEN,
                            amt=amount,
                            start=currency,
                            end=Currency.USDT
                        )
                        position[currency] = ValuePair(amount, usd_amount)
                BookKeeper.instance().updateBalance(
                    exch=Exchange.KRAKEN,
                    balance=position
                )
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
                supported_currencies_string = self.supportedCurrenciesString()
                for entry in balances:
                    if entry['asset'] in supported_currencies_string:
                        currency = Currency[entry['asset']]
                        amount = float(entry['free'])
                        usd_amount = VirtualMarket.instance().convertCurrency(
                            exch=Exchange.BINANCE,
                            amt=amount,
                            start=currency,
                            end=Currency.USDT
                        )
                        position[currency] = ValuePair(amount, usd_amount)
                BookKeeper.instance().updateBalance(
                    exch=Exchange.BINANCE,
                    balance=position
                )
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
                'pair': "{0}{1}".format(nTOk[order.pair[0].value], nTOk[order.pair[1].value]),
                'type': order.buyOrSell.value.lower(),
                'ordertype': order.orderType.value.lower(),
                'price': "%.2f" % order.price,
                'volume': str(order.volume),
            })

            #return {
            #    'pair': "{0}{1}".format(nTOk[order.pair[0].value], nTOk[order.pair[1].value]),
            #    'type': order.buyOrSell.value.lower(),
            #    'ordertype': order.orderType.value.lower(),
            #    'price': "%.2f" % order.price,
            #    'volume': str(order.volume),
            #}

        def _makeTradeBinance(self, order: Order):
            """
            Makes an API POST Request to the Binance API to place an order

            Note: If Binance receives the order at a time > timestamp + 3000 then the order is invalid
            and it will not get posted.
            """
            if not self._binance:
                raise AttributeError('Binance API instance has not been initalized')
            return self._binance.privatePostOrder({
                'symbol': "{0}{1}".format(order.pair[0].value, order.pair[1].value),
                'type': order.orderType.value,
                'timeInForce': 'GTC',
                'side': order.buyOrSell.value,
                'quantity': str(order.volume),
                'price': "%.2f" % order.price,
                'recvWindow': str(3000),
                'timestamp': str(timestamp(TimeUnit.Milliseconds))
            })

            #return {
            #    'symbol': "{0}{1}".format(order.pair[0].value, order.pair[1].value),
            #    'type': order.orderType.value,
            #    'timeInForce': 'GTC',
            #    'side': order.buyOrSell.value,
            #    'quantity': str(order.volume),
            #    'price': "%.2f" % order.price,
            #    'recvWindow': str(3000),
            #    'timestamp': str(timestamp(TimeUnit.Milliseconds))
            #}

        def makeUnsafeTrade(self, order: Order, updateBookKeeper: bool = True):
            """
            Given an Order object, will post a trade to the market.
            WARNING: Ignores all safety standards and does not check BookKeeper for our current assets
            """
            resp = None
            #if order.exchange is Exchange.KRAKEN:
            #    resp = self._makeTradeKraken(order)
            #    BookKeeper.instance().reportOrder(order=order)
            #    return resp
            #if order.exchange is Exchange.BINANCE:
            #    resp = self._makeTradeBinance(order)
            #    BookKeeper.instance().reportOrder(order=order)
            #    return resp
            #else:
            #    raise NotImplementedError('make trade is not implemented for {}'.format(order.exchange))

        def createSafeTrades(self, orders: List[Order], updateBookKeeper: bool = True):
            """
            Given a list of trades, will convert them to safe trades
            -> AKA trades that:
                - Below our maximum
                - Make sure we have enough assets to complete the trade
            """
            safe_orders = []
            
            max_vol = min([VirtualMarket.instance().convertCurrency(
                exch=order.exchange,
                amt=order.volume,
                start=order.pair[0],
                end=Currency.USDT
            ) for order in orders])

            max_vol = min(max_vol, float(SafetyValues.MaximumOrderValueUSD.value))

            for order in orders:
                required_currency = None
                if order.buyOrSell == BS.BUY:
                    required_currency = order.pair[1]
                elif order.buyOrSell == BS.SELL:
                    required_currency = order.pair[0]

                available_assets = BookKeeper.instance().getValuePairOfCurrencyInExchange(
                    exch=order.exchange,
                    curr=required_currency,
                )
                max_vol = min(max_vol, available_assets.amt_usd * 0.8)


                if max_vol < SafetyValues.MinimumOrderValueUSD.value:
                    print("Max Vol: {}".format(max_vol))
                    return None

            max_vol = VirtualMarket.instance().convertCurrency(
                                exch=order.exchange,
                                amt=max_vol,
                                start=Currency.USDT,
                                end=order.pair[0]
                            )
            max_vol = float(self._binance.amount_to_precision("{0}/{1}".format(order.pair[0].value, order.pair[1].value), max_vol))

            for order in orders:
                safe_orders.append(
                    Order(
                        exchange=order.exchange,
                        buyOrSell=order.buyOrSell,
                        orderType=order.orderType,
                        pair=order.pair,
                        price=(order.price*0.999),
                        volume=max_vol,
                    )
                )

            return safe_orders


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