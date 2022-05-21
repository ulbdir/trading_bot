from asyncio.log import logger
from datetime import datetime
from sqlite3 import Timestamp
import string
import time

import pandas
from Market import Market
from Order import Order
from PriceProvider import PriceProvider
from SimulatedBroker import SimulatedBroker

class BacktestingPriceProvider(PriceProvider):

    def __init__(self, exchange, market: Market, broker: SimulatedBroker, timeframe: string, start_date: datetime, end_date: datetime) -> None:
        super().__init__(exchange)
        self.timeframe=timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.market = market
        self.broker = broker

        # initialise current price
        self.current_price = 0
        self.current_time = start_date
        candles = exchange.fetch_ohlcv (market.get_market(), self.timeframe, since=start_date.timestamp()*1000, limit=1 )
        for candle in candles:
            self.current_price = candle[1]
            self.current_time = datetime.utcfromtimestamp(candle[0] / 1000)

    def getCurrentPrice(self, pair: Market) -> float:
        return float(self.current_price)

    def updatePriceListenersWithBacktestingData(self, price, timestamp):
        for pair, l in self.listeners.items():
            if pair == self.market:
                for cl in l:
                    cl.onPriceChanged(self.market, price, timestamp)

    def run(self):
        current_time = self.start_date.timestamp()*1000
        stop_time = self.end_date.timestamp() * 1000
        
        logger.info("Backtesting started")
        logger.info("Downloading candles")

        candles_df = pandas.DataFrame(columns=["date", "open", "high", "low", "close", "volume"]).set_index("date")

        while current_time < stop_time:
            logger.info("Backtesting from " + self.start_date.strftime("%Y %m %d") + " to " + self.end_date.strftime("%Y %m %d") + ", progress " + datetime.utcfromtimestamp(current_time / 1000).strftime("%Y %m %d"))
            candles = self.exchange.fetch_ohlcv (self.market.get_market(), self.timeframe, since=current_time)

            # convert lists to dataframe
            df = pandas.DataFrame(candles, columns=["date", "open", "high", "low", "close", "volume"])

            # convert timestamp to datetime
            df['date'] = pandas.to_datetime(df['date'], unit='ms', utc=True, infer_datetime_format=True)

            # convert price values to float
            df = df.astype(dtype={'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float',
                                    'volume': 'float'})

            df.set_index("date", inplace=True)

            candles_df = pandas.concat([candles_df, df], ignore_index=False)
            
            # remove duplicate candles
            candles_df = candles_df[~candles_df.index.duplicated(keep='last')]

            # update last downloaded candle timestamp
            last_candle_date = df.index[-1]
            current_time = int(last_candle_date.timestamp() * 1000)

        # filter out candles after end_date
        candles_df = candles_df[(candles_df.index <= self.end_date)]

        logger.info(str.format("Downloaded {} candles", len(candles_df.index)))

        # go through all rows and simulate price movement
        for index, row in candles_df.iterrows():
            if row["close"] > row["open"]:
                # green candle, price plays open->low->high->close
                self.simulate_price_movement(row["open"], row["low"], index)
                self.simulate_price_movement(row["low"], row["high"], index)
                self.simulate_price_movement(row["high"], row["close"], index)
            else:
                # red candle, price plays open->high->low->close
                self.simulate_price_movement(row["open"], row["high"], index)
                self.simulate_price_movement(row["high"], row["low"], index)
                self.simulate_price_movement(row["low"], row["close"], index)
            self.current_price = row["close"]

        self.historic_candles = candles_df
        logger.info("Backtesting complete")

    def simulate_price_movement(self, a: float, b: float, timestamp) -> None:
        """Simulates price moving from a to b"""
        # 1. get orders that will be filled if price moves from a to b
        # 2. simulate a price event at the limit price of each order, in correct order
        #    market orders can be ignored, they will be filled at the next price event anyway

        logger.debug(str.format("Simulate price point {}", a))
        self.updatePriceListenersWithBacktestingData(a, timestamp)

        last_simulated_price = a
        orders = self.broker.get_open_orders(last_simulated_price, b)
        while len(orders) > 0:
            if a > b:
                # sort orders by limit price descending
                orders.sort(key=lambda o: o.limit_price, reverse=True)
            else:
                # sort orders by limit price ascending
                orders.sort(key=lambda o: o.limit_price)
            
            # simulate a price change on the limit price of the next order that would be filled
            for order in orders:
                if order.type == Order.Type.LIMIT and order.limit_price > 0:
                    self.updatePriceListenersWithBacktestingData(order.limit_price, timestamp)
                    logger.debug(str.format("Simulate additonal price point {}", order.limit_price))
                    last_simulated_price = order.limit_price
                    break
            orders = self.broker.get_open_orders(last_simulated_price, b)
        