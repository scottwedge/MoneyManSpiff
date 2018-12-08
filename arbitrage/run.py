from arbitrage_engine import ArbitrageEngine
from market_engine import MarketEngine
from constants import Currency
from virtual_market import VirtualMarket

from pprint import pprint
from time import sleep

def run():
    exchanges = MarketEngine.instance().supportedExchanges()
    pairs = MarketEngine.instance().supportedCurrencyPairs()
    while True:
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
                ArbitrageEngine.instance().verifyArbitrage(path=arbitrage_path)
                orders = ArbitrageEngine.instance().pathToOrders(
                    path=arbitrage_path,
                    graph=ArbitrageEngine.instance()._graph)
                pprint(orders)
            else:
                print("{0}No arbitrage opportunity found!{1}\n".format('\033[91m','\033[0m'))

            sleep(5)

        except Exception as e:
            pprint(e)
            break

if __name__ == '__main__':
    run()