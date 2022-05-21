import logging
import math
import string
from Broker import Broker, BrokerListener
from Grid import Grid
from Market import Market
from Order import Order
from OrderFill import OrderFill
from PriceProvider import PriceListener, PriceProvider
from SimulatedBroker import SimulatedBroker
from Strategy import Strategy
from Wallet import Wallet

class GridStrategy(Strategy, BrokerListener):

    def __init__(self, pair: Market, wallet: Wallet, broker: Broker, price_provider: PriceProvider) -> None:
        super().__init__()
        self.pair = pair
        self.wallet = wallet
        self.broker = broker
        self.price_provider = price_provider

    def initialiseOrders(self) -> None:
        market_price = self.price_provider.getCurrentPrice(self.pair)
        logging.info("Current market price for " + self.pair.base_currency + " is " + str(market_price))
        
        value_base = self.wallet.getBalance(self.pair.base_currency) * market_price
        value_quote = self.wallet.getBalance(self.pair.quote_currency)
        logging.info(self.pair.base_currency + " value is " + str(value_base))
        logging.info(self.pair.quote_currency + " value is " + str(value_quote))

        size_per_grid = (value_base + value_quote) / len(self.grid.grid_lines)
        logging.info("Position size per grid line " + str(size_per_grid))
        
        test_qty = size_per_grid / self.grid.grid_lines[1]
        logging.info("Profit per sell order " + str(test_qty * self.grid.grid_lines[0] - test_qty * self.grid.grid_lines[1]))

        logging.info(self.pair.base_currency + " value required for " + str(self.grid.num_gridlines_above(market_price)) + " sell orders: " + str(self.grid.num_gridlines_above(market_price) * size_per_grid))
        logging.info(self.pair.quote_currency + " value required for " + str(self.grid.num_gridlines_below(market_price)) + " buy orders: " + str(self.grid.num_gridlines_below(market_price) * size_per_grid))

        value_base_to_buy = self.grid.num_gridlines_above(market_price) * size_per_grid - value_base
        if value_base_to_buy > 0:
            base_qty = value_base_to_buy / market_price
            self.broker.createOrder(self.pair, base_qty)
        
        # create buy order below
        if market_price > self.grid.lower_price:
            buy_price = self.grid.price_below(market_price)
            buy_qty = size_per_grid / buy_price
            self.broker.createOrder(self.pair, buy_qty, Order.Side.BUY, Order.Type.LIMIT, buy_price)

        # create sell order above
        if market_price < self.grid.upper_price:
            sell_price = self.grid.price_above(market_price)
            # sell the qty that was bought one level below
            buy_price = market_price
            if market_price > self.grid.lower_price:
                buy_price = self.grid.price_below(market_price)
            else:
                buy_price = self.grid.lower_price
            
            sell_qty = size_per_grid / buy_price

            self.broker.createOrder(self.pair, sell_qty, Order.Side.SELL, Order.Type.LIMIT, sell_price)


    def initialise(self) -> None:
        self.grid = Grid(35000, 25000, 500)
        self.initialiseOrders()

    def onOrderFilled(self, order: Order, fill: OrderFill):
        if (order.type == Order.Type.LIMIT) and (order.market == self.pair):
            self.broker.cancel_all_orders(self.pair)
            idx = self.grid.get_grid_index(order.limit_price)
            if idx >= 0:
                market_price = order.limit_price

                value_base = self.wallet.getBalance(self.pair.base_currency) * market_price
                value_quote = self.wallet.getBalance(self.pair.quote_currency)

                size_per_grid = (value_base + value_quote) / len(self.grid.grid_lines)
                
                # create buy order one grid level below
                below_idx = idx + 1
                if below_idx < len(self.grid.grid_lines):
                    buy_price = self.grid.grid_lines[below_idx]
                    buy_qty = size_per_grid / buy_price
                    self.broker.createOrder(self.pair, buy_qty, Order.Side.BUY, Order.Type.LIMIT, buy_price)

                # create sell order above
                sell_idx = idx - 1
                if sell_idx >= 0:
                    sell_price = self.grid.grid_lines[sell_idx]
                    # sell the qty that was bought on current level
                    sell_qty = size_per_grid / self.grid.grid_lines[idx]
                    self.broker.createOrder(self.pair, sell_qty, Order.Side.SELL, Order.Type.LIMIT, sell_price)
        else:
            logging.info("Order ignored: " + str(order))

