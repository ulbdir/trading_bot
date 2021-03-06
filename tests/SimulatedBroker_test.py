from Market import Market
from SimulatedBroker import SimulatedBroker
from Order import Order
import unittest

from Wallet import Wallet

class Test_SimulatedBroker(unittest.TestCase):
    
    def setUp(self) -> None:
        self.wallet = Wallet()
        self.broker = SimulatedBroker(self.wallet)
        self.market = Market("BTC", "USD")
        return super().setUp()
    
    def test_createOrder(self):
        o = self.broker.createOrder(self.market, 1)
        self.assertIn(o, self.broker.open_orders)
        self.assertTrue(len(self.broker.filled_orders) == 0)

        o2 = self.broker.createOrder(self.market, 1)
        self.assertNotEqual(o, o2)
        self.assertNotEqual(o.id, o2.id)
        self.assertEqual(o, o.id)
        self.assertEqual(o2, o2.id)

    def test_cancelOrder(self):
        # create order and cancel it
        o = self.broker.createOrder(self.market, 1)
        self.assertIn(o, self.broker.open_orders)

        self.broker.cancelOrder(o.id)
        self.assertNotIn(o, self.broker.open_orders)

        # test order id that does not exist
        self.broker.cancelOrder(100)

    def test_onPriceChanged_MarketOrder(self):
        # market buy
        o_buy = self.broker.createOrder(self.market, 1)
        o_sell = self.broker.createOrder(self.market, 1, Order.Side.SELL)

        self.assertIn(o_buy, self.broker.open_orders)
        self.assertIn(o_sell, self.broker.open_orders)

        self.broker.onPriceChanged(self.market, 1)

        self.assertNotIn(o_buy, self.broker.open_orders)
        self.assertNotIn(o_sell, self.broker.open_orders)

        self.assertIn(o_buy, self.broker.filled_orders)
        self.assertIn(o_sell, self.broker.filled_orders)

    def test_onPriceChanged_LimitOrder_Long(self):
        o = self.broker.createOrder(self.market, 1, Order.Side.BUY, Order.Type.LIMIT, 100)
        self.assertIn(o, self.broker.open_orders)

        # change price, but above limit price -> limit order not executed
        self.broker.onPriceChanged(self.market, 200)
        self.assertIn(o, self.broker.open_orders)
        self.assertNotIn(o, self.broker.filled_orders)

        # lower price below limit price -> limit order is executed
        self.broker.onPriceChanged(self.market, 50)
        self.assertNotIn(o, self.broker.open_orders)
        self.assertIn(o, self.broker.filled_orders)

    def test_onPriceChanged_LimitOrder_Short(self):
        o = self.broker.createOrder(self.market, 1, Order.Side.SELL, Order.Type.LIMIT, 100)
        self.assertIn(o, self.broker.open_orders)

        # change price, but below limit price -> limit order not executed
        self.broker.onPriceChanged(self.market, 50)
        self.assertIn(o, self.broker.open_orders)
        self.assertNotIn(o, self.broker.filled_orders)

        # change price above limit price -> limit order is executed
        self.broker.onPriceChanged(self.market, 150)
        self.assertNotIn(o, self.broker.open_orders)
        self.assertIn(o, self.broker.filled_orders)
