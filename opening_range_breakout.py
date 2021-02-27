import sqlite3
import config
import alpaca_trade_api as tradeapi
from datetime import date, timedelta
import pandas as pd

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row 

cursor = connection.cursor()

cursor.execute("""
	SELECT id FROM strategy
	WHERE name = 'opening_range_breakout'
	""")

strategy_id = cursor.fetchone()['id']

cursor.execute("""
	SELECT symbol, name
	FROM stock JOIN stock_strategy
		ON stock_strategy.stock_id = stock.id
	WHERE stock_strategy.strategy_id = ?
	""", (strategy_id,))

stocks = cursor.fetchall()
symbols =  [stock['symbol'] for stock in stocks]

# Contact with the API
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)


current_date = (date.today() - timedelta(days=1)).isoformat()
start_minute_bar = f"{current_date} 9:30:00"
end_minute_bar   = f"{current_date} 9:45:00"

for symbol in symbols:
	minute_bars = api.get_barset(symbol, '1Min', 200, start = start_minute_bar, end = end_minute_bar).df

	print(symbol)
	opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
	opening_range_bars = minute_bars.loc[opening_range_mask]
	print(opening_range_bars)

	opening_range_low = opening_range_bars[symbol, 'low'].min()
	opening_range_high = opening_range_bars[symbol, 'high'].max()
	opening_range = opening_range_high - opening_range_low
	print(opening_range_high)
	print(opening_range_low)
	print(opening_range)

