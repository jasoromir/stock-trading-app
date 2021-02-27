import sqlite3
import alpaca_trade_api as tradeapi
import config

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)

# Obtain assets
assets = api.list_assets()

# Establish connection with our database
connection = sqlite3.connect(config.DB_FILE)

connection.row_factory = sqlite3.Row #This converts rows to objects

cursor = connection.cursor()

cursor.execute("""
	SELECT * FROM stock
	""")

rows = cursor.fetchall()
symbols = [row['symbol'] for row in rows]


for asset in assets:
	try:
		if asset.tradable and asset.status == 'active' and asset.symbol not in symbols:
			print(f"Added a new stock {asset.symbol} {asset.name}")
			cursor.execute("""
				INSERT INTO stock (symbol, name, exchange) VALUES (?,?,?)
				""", (asset.symbol, asset.name, asset.exchange))
	except Exception as e:
		print(asset.symbol)
		print(e)

connection.commit()



