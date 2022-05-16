import logging
import math
import string
from Broker import Broker
from Market import Market
from Order import Order
from OrderFill import OrderFill
from PriceProvider import PriceListener, PriceProvider
from SimulatedBroker import SimulatedBroker
from Strategy import Strategy
from Wallet import Wallet

class GridStrategy(Strategy, PriceListener):

    def __init__(self, pair: Market, wallet: Wallet, broker: Broker, price_provider: PriceProvider) -> None:
        super().__init__()
        self.pair = pair
        self.wallet = wallet
        self.broker = broker
        self.price_provider = price_provider
        self.grid_lines = []
        self.upper_price = 40000
        self.lower_price = 15000
        self.price_step = 100


    def initialiseGrid(self, upper_price:float, lower_price:float, price_step: float) -> None:

        # make sure upper price is greater than lower price
        if upper_price < lower_price:
            raise ValueError()

        # initialise grid lines
        self.grid_lines = []
        price = upper_price
        while (price >= lower_price):
            self.grid_lines.append(price)
            price -= price_step
        logging.info("Generated " + str(len(self.grid_lines)) + " price levels from " + str(self.upper_price) + " to " + str(self.lower_price) + " every " + str(self.price_step))
        logging.debug(self.grid_lines)

    def num_gridlines_below(self, price: float) -> int:
        if price > self.lower_price:
            return math.floor((price - self.lower_price) / self.price_step) + 1
        else:
            return 0

    def num_gridlines_above(self, price) -> int:
        if price < self.upper_price:
            return math.floor((self.upper_price - price) / self.price_step) + 1
        else:
            return 0

    # return price for level below given price
    def price_below(self, price) -> float:
        return math.floor(price / self.price_step) * self.price_step

    # return price for level above given price
    def price_above(self, price) -> float:
        return math.ceil(price / self.price_step) * self.price_step

    def get_grid_index(self, price: float):
        
        # find nearest price in terms of price_step
        nearest_grid_price = round(price / self.price_step) * self.price_step
        idx = round((nearest_grid_price - self.lower_price) / self.price_step)
        
        # since prices are sorted high to low, the idx is actually from the end of the grid and needs to be reverted
        idx = len(self.grid_lines) - idx - 1
        
        # clamp to grid range
        idx = min(idx, len(self.grid_lines)-1)
        idx = max(idx, 0)

        return idx


    def initialiseOrders(self) -> None:
        market_price = self.price_provider.getCurrentPrice(self.pair)
        logging.info("Current market price for " + self.pair.base_currency + " is " + str(market_price))
        
        value_base = self.wallet.getBalance(self.pair.base_currency) * market_price
        value_quote = self.wallet.getBalance(self.pair.quote_currency)
        logging.info(self.pair.base_currency + " value is " + str(value_base))
        logging.info(self.pair.quote_currency + " value is " + str(value_quote))

        size_per_grid = (value_base + value_quote) / len(self.grid_lines)
        logging.info("Position size per grid line " + str(size_per_grid))
        
        test_qty = size_per_grid / self.grid_lines[1]
        logging.info("Profit per sell order " + str(test_qty * self.grid_lines[0] - test_qty * self.grid_lines[1]))

        logging.info(self.pair.base_currency + " value required for " + str(self.num_gridlines_above(market_price)) + " sell orders: " + str(self.num_gridlines_above(market_price) * size_per_grid))
        logging.info(self.pair.quote_currency + " value required for " + str(self.num_gridlines_below(market_price)) + " buy orders: " + str(self.num_gridlines_below(market_price) * size_per_grid))

        value_base_to_buy = self.num_gridlines_above(market_price) * size_per_grid - value_base
        if value_base_to_buy > 0:
            base_qty = value_base_to_buy / market_price
            self.broker.createOrder(self.pair, base_qty)
        
        # create buy order below
        buy_price = self.price_below(market_price)
        buy_qty = size_per_grid / buy_price
        self.broker.createOrder(self.pair, buy_qty, Order.Side.BUY, Order.Type.LIMIT, buy_price)

        # create sell order above
        sell_price = self.price_above(market_price)
        # sell the qty that was bought one level below
        sell_qty = buy_qty
        self.broker.createOrder(self.pair, sell_qty, Order.Side.SELL, Order.Type.LIMIT, sell_price)


    def initialise(self) -> None:
        self.initialiseGrid(self.upper_price, self.lower_price, self.price_step)
        self.initialiseOrders()

    def onOrderFilled(self, order: Order, fill: OrderFill):
        if (order.type == Order.Type.LIMIT) and (order.market == self.pair):
            self.broker.cancel_all_orders(self.pair)
            idx = self.get_grid_index(order.limit_price)
            if idx >= 0:
                market_price = order.limit_price

                value_base = self.wallet.getBalance(self.pair.base_currency) * market_price
                value_quote = self.wallet.getBalance(self.pair.quote_currency)

                size_per_grid = (value_base + value_quote) / len(self.grid_lines)
                
                # create buy order one grid level below
                below_idx = idx + 1
                if below_idx < len(self.grid_lines):
                    buy_price = self.grid_lines[below_idx]
                    buy_qty = size_per_grid / buy_price
                    self.broker.createOrder(self.pair, buy_qty, Order.Side.BUY, Order.Type.LIMIT, buy_price)

                # create sell order above
                sell_idx = idx - 1
                if sell_idx >= 0:
                    sell_price = self.grid_lines[sell_idx]
                    # sell the qty that was bought on current level
                    sell_qty = size_per_grid / self.grid_lines[idx]
                    self.broker.createOrder(self.pair, sell_qty, Order.Side.SELL, Order.Type.LIMIT, sell_price)
        else:
            logging.info("Order ignored: " + str(order))

    def onPriceChanged(self, pair: string, price: float):
        #print(pair, price)
        pass

