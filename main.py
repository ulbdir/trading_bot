import logging
import ccxt
import finplot

from datetime import datetime, timezone
from BacktestingPriceProvider import BacktestingPriceProvider
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
#price_provider = PriceProvider(exchange)
price_provider = BacktestingPriceProvider(exchange, market, "1h", datetime(2022, 1, 1, tzinfo=timezone.utc), datetime(2022, 4, 30, tzinfo=timezone.utc))

strategy: Strategy = GridStrategy(market, wallet, broker, price_provider)
strategy.upper_price = 50000
strategy.lower_price = 20000
strategy.price_step = 100
strategy.initialise()

broker.addListener(strategy)
price_provider.addListener(strategy, market)
price_provider.addListener(broker, market)

# run the backtest
price_provider.run()

logging.info(str.format("Wallet value: {} {}", wallet.getBalance(market.quote_currency) + wallet.getBalance(market.base_currency) * price_provider.getCurrentPrice(market), market.quote_currency))

# open a window to visualise the simulation result
# TODO add grid lines and trades to candlestick chart, add portfolio/time value as additional graph
finplot.candlestick_ochl(price_provider.historic_candles[['open', 'close', 'high', 'low']])
finplot.show()
