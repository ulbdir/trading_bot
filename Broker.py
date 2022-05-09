from abc import ABC, abstractmethod
from Order import Order

class BrokerListener(ABC):
    
    @abstractmethod
    def onOrderFilled(self, order: Order) -> None:
        pass


class Broker(ABC):

    def __init__(self) -> None:
        self.listeners: list[BrokerListener] = []

    def addListener(self, listener: BrokerListener):
        self.listeners.append(listener)
    
    def removeListener(self, listener: BrokerListener):
        self.listeners.remove(listener)

    def notifyOrderFilled(self, order: Order) -> None:
        for l in self.listeners:
            l.onOrderFilled(order)

    @abstractmethod
    def createOrder(self, qty, side: Order.Side = Order.Side.LONG, type: Order.Type = Order.Type.MARKET, limit_price: float = 0) -> Order:
        pass

    @abstractmethod
    def cancelOrder(self, order_id: int):
        pass
    
    @abstractmethod
    def onPriceChanged(self, price: float):
        pass
