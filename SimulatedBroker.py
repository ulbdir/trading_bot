from datetime import datetime, timezone
from distutils.log import WARN
import logging
from typing import overload
from Market import Market
from Order import Order
from Broker import Broker
from OrderFill import OrderFill
from PriceProvider import PriceListener
from Wallet import Wallet

class SimulatedBroker(Broker, PriceListener):

    next_id: int = 1

    def __init__(self, wallet: Wallet) -> None:
        super().__init__()
        self.wallet = wallet
        self.open_orders = []
        self.filled_orders = []
        self.logger = logging.Logger("SimulatedBroker", level = WARN)

    def createOrder(self, market: Market, qty: float, side: Order.Side = Order.Side.BUY, type: Order.Type = Order.Type.MARKET, limit_price: float = 0, timestamp = None) -> Order:
        result = Order(market, qty, side, type, limit_price, timestamp)
        
        # assign unique id
        result.id = SimulatedBroker.next_id
        SimulatedBroker.next_id += 1

        self.open_orders.append(result)

        self.logger.info("Order created: " + str(result))

        return result

    def cancelOrder(self, order_id: int):
        if order_id in self.open_orders:
            self.open_orders.remove(order_id)
            self.logger.info("Order canceled: " + str(order_id))
        else:
            self.logger.warning("cancelOrder: Order not found: " + str(order_id))
    
    def _generate_complete_fill(self, order: Order, price: float, timestamp) -> OrderFill:
        fill = OrderFill(order.qty, price, 0, timestamp)
        return fill

    def _add_fill(self, order: Order, fill: OrderFill):
        
        # modify wallet
        if order.side == Order.Side.BUY:
            # buy order increases base currency and decreases quote currency (+BTC -USD)
            base = self.wallet.getBalance(order.market.base_currency)
            self.wallet.setBalance(order.market.base_currency, base + fill.qty)

            quote = self.wallet.getBalance(order.market.quote_currency)
            self.wallet.setBalance(order.market.quote_currency, quote - fill.qty * fill.price)
        else:
            # sell order decreases base currency and increases quote currency (-BTC +USD)
            base = self.wallet.getBalance(order.market.base_currency)
            self.wallet.setBalance(order.market.base_currency, base - fill.qty)

            quote = self.wallet.getBalance(order.market.quote_currency)
            self.wallet.setBalance(order.market.quote_currency, quote + fill.qty * fill.price)

        # add fill to order
        order.fills.append(fill)
        if order.is_filled():
            self.filled_orders.append(order)
            self.logger.info("Order filled: " + str(order))
        
        self.logger.info(str(self.wallet))

    def onPriceChanged(self, pair: Market, price: float, timestamp = None):
        remaining_orders = []
        notifications = []
        for order in self.open_orders:
            if order.market == pair:
                if order.type == Order.Type.MARKET:
                    # execute any market order
                    fill = self._generate_complete_fill(order, price, timestamp)
                    self._add_fill(order, fill)
                elif order.type == Order.Type.LIMIT:
                    # check limit orders
                    if order.side == Order.Side.BUY:
                        # buy order is executed when the price is lower than the limit price
                        if price <= order.limit_price:
                            fill = self._generate_complete_fill(order, price, timestamp)
                            self._add_fill(order, fill)
                            notifications.append([order, fill])
                        else:
                            remaining_orders.append(order)
                    else:
                        # sell order is executed when price is greater than limit price
                        if price >= order.limit_price:
                            fill = self._generate_complete_fill(order, price, timestamp)
                            self._add_fill(order, fill)
                            notifications.append([order, fill])
                        else:
                            remaining_orders.append(order)
                else:
                    # unknown order type
                    pass
        self.open_orders = remaining_orders

        # do notifications
        for n in notifications:
            self.notifyOrderFilled(n[0], n[1])

    def get_open_orders(self, a: float, b: float) -> list[Order]:
        """
            Retuns all orders that would be filled when price moves from a to b
            TODO: Seems to work, but this method needs tests!
        """
        result: list[Order] = []
        min_price = min(a, b)
        max_price = max(a, b)
        for order in self.open_orders:

            # market order is always filled
            if order.type == Order.Type.MARKET:
                result.append(order)
            
            # check limit price for limit orders
            elif order.type == Order.Type.LIMIT:
                if order.side == Order.Side.BUY:
                    # buy orders are executed when
                    # - the limit price is greater than b for red candles
                    # - the limit price is greater than a for green candles
                    if order.limit_price >= min_price:
                        result.append(order)
                if order.side == Order.Side.SELL:
                    # sell orders are executed when
                    # - the limit price is less than a for red candles
                    # - the limit price is less than b for green candles
                    if order.limit_price <= max_price:
                        result.append(order)
            else:
                pass
        return result

    def cancel_all_orders(self, market: Market):
        remaining_orders = []
        for order in self.open_orders:
            if order.market == market:
                # cancel this order
                self.logger.info("Order canceled: " + str(order))
            else:
                remaining_orders.append(order)
        self.open_orders = remaining_orders
