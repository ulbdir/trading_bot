from abc import ABC, abstractmethod
import string
from Market import Market
from Order import Order
from OrderFill import OrderFill

class BrokerListener(ABC):
    
    @abstractmethod
    def onOrderFilled(self, order: Order, fill: OrderFill) -> None:
        pass


class Broker(ABC):

    def __init__(self) -> None:
        self.listeners: list[BrokerListener] = []

    def addListener(self, listener: BrokerListener):
        self.listeners.append(listener)
    
    def removeListener(self, listener: BrokerListener):
        self.listeners.remove(listener)

    def notifyOrderFilled(self, order: Order, fill: OrderFill) -> None:
        for l in self.listeners:
            l.onOrderFilled(order, fill)

    @abstractmethod
    def createOrder(self, market: Market, qty: float, side: Order.Side = Order.Side.BUY, type: Order.Type = Order.Type.MARKET, limit_price: float = 0) -> Order:
        pass

    @abstractmethod
    def cancelOrder(self, order_id: int):
        pass
    