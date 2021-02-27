import sqlite3
import alpaca_trade_api as tradeapi
import config

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
	barsets = api.get_barset(symbol_request, 'day')

	for symbol in barsets:
		print(f"processing symbol {symbol}")

		for bar in barsets[symbol]:
			stock_id = stock_dict[symbol]
			cursor.execute("""
				INSERT INTO stock_price (stock_id, 'date', open, high, low, close, volume)
				VALUES (?, ?, ?, ?, ?, ?, ?)""", 
				(stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v)
				)

connection.commit()
