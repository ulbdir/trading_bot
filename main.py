import logging
import ccxt
import finplot

from datetime import datetime, timezone
from matplotlib.pyplot import legend

import pandas
from pyparsing import col
from BacktestingPriceProvider import BacktestingPriceProvider
from Equity import Equity
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
price_provider = BacktestingPriceProvider(exchange, market, broker, "1h", datetime(2022, 1, 1, tzinfo=timezone.utc), datetime(2022, 5, 21, tzinfo=timezone.utc))

strategy: Strategy = GridStrategy(market, wallet, broker, price_provider)
strategy.initialise(50000, 20000, 200)

broker.addListener(strategy)
price_provider.addListener(broker, market)

# collect equity statistics over time
equity = Equity(market, wallet, price_provider)
broker.addListener(equity)

# run the backtest
price_provider.run()

logging.info(str.format("Wallet value: {} {}", wallet.getBalance(market.quote_currency) + wallet.getBalance(market.base_currency) * price_provider.getCurrentPrice(market), market.quote_currency))

# open a window to visualise the simulation result
# TODO add trades to candlestick chart, add portfolio/time value as additional graph
ax, ax2, ax3 = finplot.create_plot(market.get_market(), rows = 3)
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

# create equity dataframe
equity_df = pandas.DataFrame(equity.equity, columns=["time", "equity"])
equity_df['time'] = pandas.to_datetime(equity_df['time'], unit='ms', utc=True, infer_datetime_format=True)

# if there are multiple sell orders per candle, we get multiple equity values per time slot. Drop these duplicates and keep the max equity value.
equity_df = equity_df.loc[equity_df.groupby(['time'])['equity'].idxmax()]
equity_df.set_index("time", inplace=True)

equity_df.equity.plot(ax = ax2, legend="equity")

# plot profit
rows = []
profit_total = 0
for order in broker.filled_orders:
    if order.closes is not None and order.side == Order.Side.SELL:
        buy_value = order.closes.qty * order.closes.fill_price()
        sell_value = order.qty * order.fill_price()
        rows.append({"time": order.get_filled_timestamp(), "profit": sell_value - buy_value})
        profit_total += sell_value - buy_value

print(profit_total)

profit_df = pandas.DataFrame(rows, columns=["time", "profit"])
profit_df["date"] = pandas.to_datetime(profit_df['time'], unit='ms', utc=True, infer_datetime_format=True)

# sum up all profits at same time slot
profit_df = profit_df.groupby("time", as_index=False).sum()

# compute cumulative sum over time
profit_df["cumulative_profit"] = profit_df["profit"].cumsum()
profit_df.set_index("time", verify_integrity=True, inplace=True)

profit_df.cumulative_profit.plot(ax=ax3, legend="cumulative profit")

finplot.show()
