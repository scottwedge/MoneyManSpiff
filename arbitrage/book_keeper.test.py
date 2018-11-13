import unittest
from book_keeper import BookKeeper
from constants import Currency, Exchange

class TestBookKeeper(unittest.TestCase):
    def test_addExchange(self):
        BookKeeper.instance().addExchange(Exchange.KRAKEN)
        try:
            BookKeeper.instance().addExchange(Exchange.KRAKEN)
        except:
            self.assertTrue(True)
        self.assertEqual(BookKeeper.instance().getPositions(), {
            Exchange.KRAKEN: {}
            }
        )
        BookKeeper.instance().clear()
    
    def test_addCurrencyToExchange(self):
        BookKeeper.instance().addExchange(Exchange.KRAKEN)
        BookKeeper.instance().addCurrencyToExchange(
            exch=Exchange.KRAKEN,
            curr=Currency.BCH,
            value_pair=(1,1)
        )
        try:
            BookKeeper.instance().addCurrencyToExchange(
                exch=Exchange.BINANCE, 
                curr=Currency.BTC,
                value_pair=(0,0)
            )
        except:
            self.assertTrue(True)
        self.assertEqual(BookKeeper.instance().getPositions(), {
            Exchange.KRAKEN: {
                Currency.BCH: (1, 1)
            }
        })
        BookKeeper.instance().clear()

    def test_updatePosition(self):
        BookKeeper.instance().addExchange(Exchange.BINANCE)
        BookKeeper.instance().addCurrencyToExchange(
            exch=Exchange.BINANCE,
            curr=Currency.BTC,
            value_pair=(1,1)
        )
        BookKeeper.instance().addCurrencyToExchange(
            exch=Exchange.BINANCE,
            curr=Currency.ETH,
            value_pair=(0,0)
        )
        mockPosition = {
            Currency.BTC: (50, 20),
            Currency.ETH: (100, 100),
        }
        BookKeeper.instance().updatePosition(
            exch=Exchange.BINANCE,
            position=mockPosition
        )
        self.assertEqual(BookKeeper.instance().getPositions(), {
            Exchange.BINANCE: {
                Currency.BTC: (50, 20),
                Currency.ETH: (100, 100),
            }
        })

if __name__ == '__main__':
    unittest.main()