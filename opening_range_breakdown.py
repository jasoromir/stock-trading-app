import sqlite3
import config
import alpaca_trade_api as tradeapi
from datetime import date, timedelta
from timezone import is_dst
import pandas as pd
import smtplib, ssl # Sending email from python


# Create a secure SSL context for sending emails
context = ssl.create_default_context()

# Connect with our database
connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row 

# Querries to select stocks from desired strategy
cursor = connection.cursor()

cursor.execute("""
	SELECT id FROM strategy
	WHERE name = 'opening_range_breakdown'
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


# Modify current date to operate
current_date = date.today()- timedelta(days =1)
#If we are on a weekend, go back to Friday
if date.weekday(current_date) >=5:
	current_date = (current_date + timedelta(days =  4-date.weekday(current_date) )).isoformat()

if is_dst():
	start_minute_bar = f"{current_date} 9:30:00-05:00"
	end_minute_bar   = f"{current_date} 9:45:00-05:00"
else:
	start_minute_bar = f"{current_date} 9:30:00-04:00"
	end_minute_bar   = f"{current_date} 9:45:00-04:00"


# Contact with the API
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)


# Make sure we are not executing repeated orders
orders = api.list_orders(status='all', after=current_date)
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']


# Initialize Message to send by email
messages = []

# Loop through our list of symbols
for symbol in symbols:
	minute_bars = api.get_barset(symbol, '1Min', 500, after = start_minute_bar).df

	# print(symbol)
	# print(start_minute_bar)
	# print(minute_bars)
	opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index < end_minute_bar)
	opening_range_bars = minute_bars.loc[opening_range_mask]
	# print(opening_range_bars)

	opening_range_low = opening_range_bars[symbol, 'low'].min()
	opening_range_high = opening_range_bars[symbol, 'high'].max()
	opening_range = opening_range_high - opening_range_low
	# print(opening_range_high)
	# print(opening_range_low)
	# print(opening_range)

	after_opening_range_mask = minute_bars.index >= end_minute_bar
	after_opening_range_bars = minute_bars.loc[after_opening_range_mask]

	after_opening_range_breakdown = after_opening_range_bars[after_opening_range_bars[symbol, 'close'] < opening_range_low]

	if not after_opening_range_breakdown.empty:

		if symbol not in existing_order_symbols:
			limit_price = after_opening_range_breakdown[symbol, 'close'][0]

			print(f"Selling short {symbol} at {limit_price}, closed below {opening_range_low} at {after_opening_range_breakdown.iloc[0]}")
			messages.append(f"Selling short {symbol} at {limit_price}, closed below {opening_range_low}\n\n{after_opening_range_breakdown.iloc[0]}\n\n")

			try:
				api.submit_order(
					symbol = symbol,
					side   = 'sell',
					type   = 'limit',
					qty    = '100',
					time_in_force = 'day',
					order_class = 'bracket',
					limit_price = limit_price,
					take_profit = dict(
						limit_price = limit_price - opening_range,
						),
					stop_loss = dict(
						stop_price = limit_price + opening_range,
						)
				)
			except Exception as e:
				print(f"Couldnt submit order {e}")

		else:
			print(f"Already in order for {symbol}, skipping")

# print(messages)


with smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT, context=context) as server:

	server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
	email_message = f"Subject: Trade Notifications for {current_date}\n\n"
	email_message += "\n\n".join(messages)
	server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, email_message)
			    