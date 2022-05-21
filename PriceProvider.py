from abc import ABC, abstractmethod
import string
from Market import Market

class PriceListener(ABC):
    
    @abstractmethod
    def onPriceChanged(self, pair: Market, price: float, timestamp = None):
        pass

class PriceProvider:

    def __init__(self, exchange) -> None:
        super().__init__()
        self.listeners = {}
        self.exchange = exchange

    def addListener(self, listener: PriceListener, market: Market):
        if not market in self.listeners:
            self.listeners[market] = [listener]
        else:
            self.listeners[market].append(listener)
    
    def removeListener(self, listener: PriceListener):
        for k,v in self.listeners:
            v.remove(listener)

    def updatePriceListeners(self):
        for pair, l in self.listeners.items():
            price = self.getCurrentPrice(pair)
            for cl in l:
                cl.onPriceChanged(pair, price)

    def getCurrentPrice(self, pair: Market) -> float:
        ticker = self.exchange.fetch_ticker(pair.get_market())
        return float(ticker["last"])
