from Order import Order
from SimulatedBroker import SimulatedBroker
from Strategy import Strategy


class GridStrategy(Strategy):

    def __init__(self, upper_price:float, lower_price:float, price_step: float) -> None:
        super().__init__()

        # make sure upper price is greater than lower price
        if upper_price < lower_price:
            raise ValueError()

        self.upper_price = upper_price
        self.lower_price = lower_price
        self.price_step = price_step
        
        # initialise grid lines
        self.grid_lines = []
        price = upper_price
        while (price > lower_price):
            self.grid_lines.append(price)
            price -= price_step
        print("Generated", len(self.grid_lines), "price levels from", self.upper_price,"to",self.lower_price,"every",self.price_step)

    def onPriceChanged(self, price):
        pass

g = GridStrategy(50000, 20000, 100)