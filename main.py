import logging
import ccxt
import time
from datetime import datetime
from GridStrategy import GridStrategy
from Market import Market
from PriceProvider import PriceProvider

from SimulatedBroker import SimulatedBroker
from Strategy import Strategy
from Wallet import Wallet


logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

# The market for the bot
market = Market("BTC", "USD")

# initialise a backtesting wallet
wallet: Wallet = Wallet()
wallet.setBalance("USD", 1000)

broker: SimulatedBroker = SimulatedBroker(wallet)

exchange = ccxt.ftx()
price_provider = PriceProvider(exchange)

strategy: Strategy = GridStrategy(market, wallet, broker, price_provider)
strategy.upper_price = 40000
strategy.lower_price = 15000
strategy.price_step = 100
strategy.initialise()

price_provider.addListener(strategy, market)
price_provider.addListener(broker, market)

while True:
    price_provider.updatePriceListeners()
    time.sleep(5)

if exchange.has['fetchOHLCV']:
    while True:
        symbol = "BTC/USD"
        ticker = exchange.fetch_ticker(symbol)
        print("Ticker", ticker["last"])

        candles = exchange.fetch_ohlcv (symbol, '1h', limit=5)
        for candle in candles:
            print(datetime.now(),"   ->   ", datetime.utcfromtimestamp(candle[0] / 1000).strftime('%Y-%m-%d %H:%M:%S'), candle)
        print()
        time.sleep(5)