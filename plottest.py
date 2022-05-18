from datetime import datetime, timezone
import finplot as fplt
import numpy as np
import pandas as pd
import ccxt

exchange = ccxt.ftx()
candles = exchange.fetch_ohlcv ("BTC/USD", "1h", since=datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp()*1000 )
df = pd.DataFrame(candles, columns=["date", "open", "high", "low", "close", "volume"])

# convert timestamp to datetime
df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True, infer_datetime_format=True)

# convert price values to float
df = df.astype(dtype={'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float',
                          'volume': 'float'})

# group by date and aggregate results to eliminate duplicate candles
df = df.groupby(by='date', as_index=False, sort=True).agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'max',
})

print(df)