from asyncio.log import logger
from datetime import datetime
import string
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

        while current_time < stop_time:
            logger.info("Backtesting from " + self.start_date.strftime("%Y %m %d") + " to " + self.end_date.strftime("%Y %m %d") + ", progress " + datetime.utcfromtimestamp(current_time / 1000).strftime("%Y %m %d"))
            candles = self.exchange.fetch_ohlcv (self.market.get_market(), self.timeframe, since=current_time)
            for candle in candles:
                dcandle = { "timestamp": candle[0], "open": candle[1], "high": candle[2], "low": candle[3], "close": candle[4] }

                current_time = dcandle["timestamp"]

                if dcandle["timestamp"] < stop_time:
                    if dcandle["close"] > dcandle["open"]:
                        # green candle, price plays open->low->high->close
                        self.updatePriceListenersWithBacktestingData(dcandle["open"])
                        self.updatePriceListenersWithBacktestingData(dcandle["low"])
                        self.updatePriceListenersWithBacktestingData(dcandle["high"])
                        self.updatePriceListenersWithBacktestingData(dcandle["close"])
                    else:
                        # red candle, price plays open->high->low->close
                        self.updatePriceListenersWithBacktestingData(dcandle["open"])
                        self.updatePriceListenersWithBacktestingData(dcandle["high"])
                        self.updatePriceListenersWithBacktestingData(dcandle["low"])
                        self.updatePriceListenersWithBacktestingData(dcandle["close"])
                    self.current_price = dcandle["close"]
                else:
                    break
        
        logger.info("Backtesting complete")
