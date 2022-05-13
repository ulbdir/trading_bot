from datetime import datetime, timezone
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

    def createOrder(self, market: Market, qty: float, side: Order.Side = Order.Side.BUY, type: Order.Type = Order.Type.MARKET, limit_price: float = 0) -> Order:
        result = Order(market, qty, side, type, limit_price)
        
        # assign unique id
        result.id = SimulatedBroker.next_id
        SimulatedBroker.next_id += 1

        self.open_orders.append(result)

        logging.info("Order created: " + str(result))

        return result

    def cancelOrder(self, order_id: int):
        if order_id in self.open_orders:
            self.open_orders.remove(order_id)
            logging.info("Order canceled: " + str(order_id))
        else:
            logging.warn("cancelOrder: Order not found: " + str(order_id))
    
    def _generate_complete_fill(self, order: Order, price: float) -> OrderFill:
        fill = OrderFill(order.qty, price, 0, datetime.now(timezone.utc))
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
            logging.info("Order filled: " + str(order))
            self.notifyOrderFilled(order, fill)
        
        logging.info(str(self.wallet))

    def onPriceChanged(self, pair: Market, price: float):
        remaining_orders = []
        for order in self.open_orders:
            if order.market == pair:
                if order.type == Order.Type.MARKET:
                    # execute any market order
                    fill = self._generate_complete_fill(order, price)
                    self._add_fill(order, fill)
                elif order.type == Order.Type.LIMIT:
                    # check limit orders
                    if order.side == Order.Side.BUY:
                        # buy order is executed when the price is lower than the limit price
                        if price < order.limit_price:
                            fill = self._generate_complete_fill(order, price)
                            self._add_fill(order, fill)
                        else:
                            remaining_orders.append(order)
                    else:
                        # sell order is executed when price is greater than limit price
                        if price > order.limit_price:
                            fill = self._generate_complete_fill(order, price)
                            self._add_fill(order, fill)
                        else:
                            remaining_orders.append(order)
                else:
                    # unknown order type
                    pass
        self.open_orders = remaining_orders