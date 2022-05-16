import logging
import math
from multiprocessing.sharedctypes import Value


class Grid:

    def __init__(self, upper_price:float, lower_price:float, price_step: float) -> None:

        self.upper_price = upper_price
        self.lower_price = lower_price
        self.price_step = price_step
        self.grid_lines = []

        # make sure upper price is greater than lower price
        if upper_price < lower_price:
            raise ValueError()

        # initialise grid lines
        price = upper_price
        while (price >= lower_price):
            self.grid_lines.append(price)
            price -= price_step
        logging.info("Generated " + str(len(self.grid_lines)) + " price levels from " + str(self.upper_price) + " to " + str(self.lower_price) + " every " + str(self.price_step))
        logging.debug(self.grid_lines)

    def num_gridlines_below(self, price: float) -> int:
        """Returns the number of grid lines that are lower or equal than the given price"""
        if price <= self.lower_price:
            return 0
        elif price >= self.upper_price:
            return len(self.grid_lines)
        else:
            return math.floor((price - self.lower_price) / self.price_step) + 1


    def num_gridlines_above(self, price: float) -> int:
        """Returns the number of grid lines that are higher or equal than the given price"""
        if price <= self.lower_price:
            return len(self.grid_lines)
        elif price >= self.upper_price:
            return 0
        else:
            return math.floor((self.upper_price - price) / self.price_step) + 1

    def price_below(self, price: float) -> float:
        """Returns the next grid line below or equal the given price"""
        if price < self.lower_price:
            raise ValueError()
        elif price >= self.upper_price:
            return self.upper_price
        else:
            return math.floor(price / self.price_step) * self.price_step

    def price_above(self, price: float) -> float:
        """Returns the next grid line above or equal the given price"""
        if price <= self.lower_price:
            return self.lower_price
        elif price > self.upper_price:
            raise ValueError()
        else:
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
