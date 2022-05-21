import logging
import ccxt
import finplot

from datetime import datetime, timezone
from matplotlib.pyplot import legend

import pandas
from BacktestingPriceProvider import BacktestingPriceProvider
from GridStrategy import GridStrategy
from Market import Market
from Order import Order
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
price_provider = BacktestingPriceProvider(exchange, market, broker, "1m", datetime(2022, 5, 10, tzinfo=timezone.utc), datetime(2022, 5, 21, tzinfo=timezone.utc))

strategy: Strategy = GridStrategy(market, wallet, broker, price_provider)
strategy.initialise()

broker.addListener(strategy)
price_provider.addListener(broker, market)

# run the backtest
price_provider.run()

logging.info(str.format("Wallet value: {} {}", wallet.getBalance(market.quote_currency) + wallet.getBalance(market.base_currency) * price_provider.getCurrentPrice(market), market.quote_currency))

# open a window to visualise the simulation result
# TODO add trades to candlestick chart, add portfolio/time value as additional graph
ax = finplot.create_plot(market.get_market())
finplot.candlestick_ochl(price_provider.historic_candles[['open', 'close', 'high', 'low']])

# add grid lines to view
first_date = price_provider.historic_candles.index[0]
last_date = price_provider.historic_candles.index[-1]
for gridline in strategy.grid.grid_lines:
    line = finplot.add_line((first_date, gridline), (last_date, gridline), color='#080808', interactive=False)

# add fills to view
rows = []
for order in broker.filled_orders:
    rows.append({"date": order.get_filled_timestamp(), "price": order.limit_price, "type": "buy" if order.side == Order.Side.BUY else "sell"})

order_df = pandas.DataFrame(rows, columns=["date", "price", "type"])
buy_orders = order_df[order_df["type"] == "buy"]
buy_orders.reset_index(inplace=True)

sell_orders = order_df[order_df["type"] == "sell"]
sell_orders.reset_index(inplace=True)


ds_buy = finplot._create_datasrc(ax, buy_orders["date"], buy_orders["price"])
ds_buy.standalone = True
finplot.plot(ds_buy, style='>', width=2, color="#007700", legend="buy order filled")

ds_sell = finplot._create_datasrc(ax, sell_orders["date"], sell_orders["price"])
ds_sell.standalone = True
finplot.plot(ds_sell, style='<', width=2, color="#770000", legend="sell order filled")

finplot.show()
