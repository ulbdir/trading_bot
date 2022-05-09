from typing import overload
from Order import Order
from Broker import Broker

class SimulatedBroker(Broker):

    next_id: int = 1

    def __init__(self) -> None:
        super().__init__()
        self.open_orders = []
        self.filled_orders = []

    def createOrder(self, qty, side: Order.Side = Order.Side.LONG, type: Order.Type = Order.Type.MARKET, limit_price: float = 0) -> Order:
        result = Order(qty, side, type, limit_price)
        
        # assign unique id
        result.id = SimulatedBroker.next_id
        SimulatedBroker.next_id += 1

        self.open_orders.append(result)

        return result

    def cancelOrder(self, order_id: int):
        if order_id in self.open_orders:
            self.open_orders.remove(order_id)
            print("Order", order_id, "canceled")
        else:
            print("cancelOrder: Order", order_id, "not found")
    
    def onPriceChanged(self, price: float):
        remaining_orders = []
        for order in self.open_orders:
            if order.type == Order.Type.MARKET:
                # execute any market order
                self.filled_orders.append(order)
                print("Order", order.id, "filled")
                self.notifyOrderFilled(order)
            elif order.type == Order.Type.LIMIT:
                # check limit orders
                if order.side == Order.Side.LONG:
                    # buy order is executed when the price is lower than the limit price
                    if price < order.limit_price:
                        self.filled_orders.append(order)
                        print("Order", order.id, "filled")
                        self.notifyOrderFilled(order)
                    else:
                        remaining_orders.append(order)
                else:
                    # sell order is executed when price is greater than limit price
                    if price > order.limit_price:
                        self.filled_orders.append(order)
                        print("Order", order.id, "filled")
                        self.notifyOrderFilled(order)
                    else:
                        remaining_orders.append(order)
            else:
                # unknown order type
                pass
        self.open_orders = remaining_orders