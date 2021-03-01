import sqlite3
import alpaca_trade_api as tradeapi
import config
import numpy as np
import tulipy as ti
from datetime import date, timedelta


current_date = date.today()- timedelta(days =1)
#If we are on a weekend, go back to Friday
if date.weekday(current_date) >=5:
	current_date = (current_date + timedelta(days =  4 - date.weekday(current_date) )).isoformat()


# Connect with Database
connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row

cursor = connection.cursor()
cursor.execute(""" SELECT * FROM stock """)

rows = cursor.fetchall()
#symbols = [row['symbol'] for row in rows]
symbols = []
stock_dict = {}
for row in rows:
	symbols.append(row['symbol'])
	stock_dict[row['symbol']] = row['id']

# Connect with API
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url = config.BASE_URL)

max_request = 200

for i in range(0, len(symbols), max_request):
	symbol_request = symbols[i:i+max_request]
	barsets = api.get_barset(symbol_request, 'day', after=date.today().isoformat())

	for symbol in barsets:
		print(f"processing symbol {symbol}")

		recent_closes = np.array([bar.c for bar in barsets[symbol]])

		for bar in barsets[symbol]:
			stock_id = stock_dict[symbol]

			if len(recent_closes) >= 50 and current_date == bar.t.date().isoformat():
				sma_20 = ti.sma(recent_closes, period = 20)[-1]
				sma_50 = ti.sma(recent_closes, period = 50)[-1]
				rsi_14 = ti.rsi(recent_closes, period = 14)[-1]
			else:
				sma_20, sma_50, rsi_14 = None, None, None


			cursor.execute("""
				INSERT INTO stock_price (stock_id, 'date', open, high, low, close, volume, sma_20, sma_50, rsi_14)
				VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
				(stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v, sma_20, sma_50, rsi_14)
				)

connection.commit()
