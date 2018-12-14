from arbitrage_engine import ArbitrageEngine
from book_keeper import BookKeeper
from market_engine import MarketEngine
from constants import Currency, SafetyValues
from virtual_market import VirtualMarket

from pprint import pprint
from time import sleep

def initializeEverything():
    exchanges = MarketEngine.instance().supportedExchanges()
    pairs = MarketEngine.instance().supportedCurrencyPairs()

    try:
        marketData = {}
        for exchange in exchanges:
            marketData[exchange] = MarketEngine.instance().fetchTickers(
                exch=exchange, 
                pairs=pairs)
        VirtualMarket.instance().updateMarket(marketData=marketData)

        print("Market Initialized!")
        for key,value in VirtualMarket.instance()._market.items():
            pprint(value.print())

        for exchange in exchanges:
            MarketEngine.instance().fetchBalance(exch=exchange)
        
        print("Book Keeper Initialized!")
        pprint(BookKeeper.instance()._balances)

    except Exception as e:
        print("Initialization failed!")
        pprint(e)
        return

    return (exchanges, pairs)


def run():
    exchanges, pairs = initializeEverything()

    searchForOpportunities = True

    while searchForOpportunities:
        try:
            marketData = {}
            for exchange in exchanges:
                marketData[exchange] = MarketEngine.instance().fetchTickers(
                    exch=exchange, 
                    pairs=pairs)
            VirtualMarket.instance().updateMarket(marketData=marketData)

            ArbitrageEngine.instance().updateGraph()
            ArbitrageEngine.instance()._graph.print()
            arbitrage_path = ArbitrageEngine.instance().findArbitrage(
                graph=ArbitrageEngine.instance()._graph,
                src=Currency.USDT,
            )

            if arbitrage_path:
                percentGrowth = ArbitrageEngine.instance().verifyArbitrage(path=arbitrage_path)
                if percentGrowth >= SafetyValues.MinimumOpportunity.value:
                    orders = ArbitrageEngine.instance().pathToOrders(
                        path=arbitrage_path,
                        graph=ArbitrageEngine.instance()._graph)
                    pprint(orders)
                    safe_orders = MarketEngine.instance().createSafeTrades(orders)
                    if safe_orders:
                        print('\n{0}Safe Orders:{1}'.format('\033[92m', '\033[0m'))
                        pprint(safe_orders)
                        print('\n\n')
                        for order in safe_orders:
                            pprint(MarketEngine.instance().makeUnsafeTrade(order=order))
                            print("Executed Order: {}".format(order.toStringShort()))

                        pprint(BookKeeper.instance()._balances)

            else:
                print("{0}No arbitrage opportunity found!{1}\n".format('\033[91m','\033[0m'))

            sleep(5)

        except Exception as e:
            pprint(e)
            break

if __name__ == '__main__':
    run()