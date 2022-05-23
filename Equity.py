from Broker import BrokerListener
from Market import Market
from Order import Order
from OrderFill import OrderFill
from PriceProvider import PriceListener, PriceProvider
from Wallet import Wallet


class Equity(BrokerListener):

    def __init__(self, market: Market, wallet: Wallet, price_provider: PriceProvider) -> None:
        super().__init__()
        self._wallet = wallet
        self._price_provider = price_provider
        self._market = market
        self.equity = []

    def calculate_equity(self) -> float:
        return self._wallet.getBalance(self._market.quote_currency) + self._wallet.getBalance(self._market.base_currency) * self._price_provider.getCurrentPrice(self._market)

    # calculate equity on every order fill
    def onOrderFilled(self, order: Order, fill: OrderFill) -> None:
        self.equity.append({ "time": fill.timestamp, "equity": self.calculate_equity()})
