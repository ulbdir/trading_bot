from asyncio.log import logger
from datetime import datetime
from sqlite3 import Timestamp
import string
import time

import pandas
from Market import Market
from PriceProvider import PriceProvider

class BacktestingPriceProvider(PriceProvider):

    def __init__(self, exchange, market: Market, timeframe: string, start_date: datetime, end_date: datetime) -> None:
        super().__init__(exchange)
        self.timeframe=timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.market = market

        # initialise current price
        self.current_price = 0
        self.current_time = start_date
        candles = exchange.fetch_ohlcv (market.get_market(), self.timeframe, since=start_date.timestamp()*1000, limit=1 )
        for candle in candles:
            self.current_price = candle[1]
            self.current_time = datetime.utcfromtimestamp(candle[0] / 1000)

    def getCurrentPrice(self, pair: Market) -> float:
        return float(self.current_price)

    def updatePriceListenersWithBacktestingData(self, price):
        for pair, l in self.listeners.items():
            if pair == self.market:
                for cl in l:
                    cl.onPriceChanged(self.market, price)

    def run(self):
        current_time = self.start_date.timestamp()*1000
        stop_time = self.end_date.timestamp() * 1000
        
        logger.info("Backtesting started")
        logger.info("Downloading candles")

        candles_df = pandas.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

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

            candles_df = pandas.concat([candles_df, df], ignore_index=True)
            
            # group by date and aggregate results to eliminate duplicate candles
            candles_df = candles_df.groupby(by='date', as_index=False, sort=True).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'max',
            })
            
            last_candle_date = df["date"].iloc[-1]
            current_time = int(last_candle_date.timestamp() * 1000)

        # filter out candles after end_date
        candles_df = candles_df[(candles_df["date"] <= self.end_date)]

        logger.info(str.format("Downloaded {} candles", len(candles_df.index)))

        # go through all rows and simulate price movement
        for index, row in candles_df.iterrows():
            if row["close"] > row["open"]:
                # green candle, price plays open->low->high->close
                self.updatePriceListenersWithBacktestingData(row["open"])
                self.updatePriceListenersWithBacktestingData(row["low"])
                self.updatePriceListenersWithBacktestingData(row["high"])
                self.updatePriceListenersWithBacktestingData(row["close"])
            else:
                # red candle, price plays open->high->low->close
                self.updatePriceListenersWithBacktestingData(row["open"])
                self.updatePriceListenersWithBacktestingData(row["high"])
                self.updatePriceListenersWithBacktestingData(row["low"])
                self.updatePriceListenersWithBacktestingData(row["close"])
            self.current_price = row["close"]

        self.historic_candles = candles_df
        logger.info("Backtesting complete")
