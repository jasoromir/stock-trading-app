import sqlite3, config

# OPEN or CREATE database
connection = sqlite3.connect(config.DB_FILE)

cursor = connection.cursor()

# Basic: Table to collect stocks
cursor.execute("""
	CREATE TABLE IF NOT EXISTS stock(
		id INTEGER PRIMARY KEY,
		symbol TEXT NOT NULL UNIQUE,
		name TEXT NOT NULL,
		exchange TEXT NOT NULL,
		shortable BOOLEAN NOT NULL
		)
	""")

# Basic: Table to collect the historic price of the stocks
cursor.execute("""
	CREATE TABLE IF NOT EXISTS stock_price(
		id INTEGER PRIMARY KEY,
		stock_id INTEGER NOT NULL,
		`date` NOT NULL,
		open NOT NULL,
		high NOT NULL,
		low NOT NULL,
		close NOT NULL,
		volume NOT NULL,
		sma_20,
		sma_50,
		rsi_14,
		FOREIGN KEY (stock_id) REFERENCES stock (id)
		)
	""")

# Advanced: Table to store strategies
cursor.execute("""
	CREATE TABLE IF NOT EXISTS strategy(
		id INTEGER PRIMARY KEY,
		name NOT NULL UNIQUE
		)
	""")

# Advanced: Populate table with strategies
strategies = ['opening_range_breakout', 'opening_range_breakdown']

for strategy in strategies:
	cursor.execute("""
		INSERT INTO strategy (name) VALUES (?)
		""", (strategy,))

# Advanced: Create table to populate with the stocks that fall into each strategy
cursor.execute("""
	CREATE TABLE IF NOT EXISTS stock_strategy(
		id INTEGER PRIMARY KEY,
		stock_id INTEGER NOT NULL,
		strategy_id INTEGER NOT NULL,
		FOREIGN KEY (stock_id) REFERENCES stock (id)
		FOREIGN KEY (strategy_id) REFERENCES strategy (id)
		)
	""")

# Commit changes to the database
connection.commit()