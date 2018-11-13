import unittest
from unittest.mock import MagicMock
from market_engine import MarketEngine
from constants import Currency, Exchange
import ccxt

class TestMarketEngine(unittest.TestCase):
    def test_fetchKrakenBalance(self):
        MarketEngine.instance()._kraken.privatePostBalance = MagicMock()
        MarketEngine.instance()._kraken.privatePostBalance.return_value = {
            'error': [],
            'result': {
                'XETH': '0.998374',
                'XXRP': '3024',
                'XEOS': '10984',
            }
        }
        self.assertEqual(MarketEngine.instance().fetchBalance(Exchange.KRAKEN), {
            Currency.ETH: ('0.998374', '0.998374'),
            Currency.XRP: ('3024', '3024'),
            Currency.EOS: ('10984', '10984'),
        })

    def test_fetchBinanceBalance(self):
        MarketEngine.instance()._binance.privateGetAccount = MagicMock()
        MarketEngine.instance()._binance.privateGetAccount.return_value = {
            "makerCommission": 15,
            "takerCommission": 15,
            "buyerCommission": 0,
            "sellerCommission": 0,
            "canTrade": True,
            "canWithdraw": True,
            "canDeposit": True,
            "updateTime": 123456789,
            "balances": [
                {
                    "asset": "ETH",
                    "free": "0.8893",
                    "locked": "0.00000000"
                },
                {
                    "asset": "XRP",
                    "free": "987",
                    "locked": "0.00000000"
                },
                {
                    "asset": "EOS",
                    "free": "2034",
                    "locked": "0.00000000"
                }
            ]
        }
        self.assertEqual(MarketEngine.instance().fetchBalance(Exchange.BINANCE), {
            Currency.ETH: ('0.8893', '0.8893'),
            Currency.XRP: ('987', '987'),
            Currency.EOS: ('2034', '2034'),
        })

    def test_supportedCurrencies(self):
        supported_currencies = MarketEngine.instance().supportedCurrencies()
        self.assertEqual(supported_currencies, [
            Currency.USDT, Currency.EOS, Currency.XRP,
        ])

if __name__ == '__main__':
    unittest.main()