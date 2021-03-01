import sqlite3, config
from fastapi import FastAPI, Request, Form 
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from datetime import date, timedelta
import alpaca_trade_api as tradeapi

# https://pypi.org/project/alpaca-trade-api/                 # Alpaca trading API
# https://semantic-ui.com/introduction/advanced-usage.html   # Easy template html
# https://www.tradingview.com/widget/advanced-chart/		 # Stock charts

current_date = date.today()- timedelta(days =1)
#If we are on a weekend, go back to Friday
if date.weekday(current_date) >=5:
	current_date = (current_date + timedelta(days =  4 - date.weekday(current_date) )).isoformat()

print(current_date)
app = FastAPI()
templates = Jinja2Templates(directory = "templates")

@app.get("/")
def index(request: Request):
	stock_filter = request.query_params.get('filter', False)

	connection = sqlite3.connect(config.DB_FILE)
	connection.row_factory = sqlite3.Row #This converts rows to objects

	cursor = connection.cursor()

	# Filter stocks to display
	if stock_filter == "new_closing_highs":
		cursor.execute("""
			SELECT * FROM (
				SELECT symbol, name, stock_id, max(close), date
				FROM stock_price JOIN stock 
					ON stock_price.stock_id = stock.id
				GROUP BY stock_id
				ORDER BY symbol
				)
			WHERE date = ?
			""", (current_date,))

	elif stock_filter == "new_closing_lows":
		cursor.execute("""
			SELECT * FROM (
				SELECT symbol, name, stock_id, min(close), date
				FROM stock_price JOIN stock 
					ON stock_price.stock_id = stock.id
				GROUP BY stock_id
				ORDER BY symbol
				)
			WHERE date = ?
			""", (current_date,))

	elif stock_filter == "rsi_overbought":
		cursor.execute("""
			SELECT symbol, name, stock_id,  date
			FROM stock_price JOIN stock 
				ON stock_price.stock_id = stock.id
			WHERE rsi_14 > 70
			AND date = ?
			ORDER BY symbol
			""", (current_date,))

	elif stock_filter == "rsi_oversold":
		cursor.execute("""
			SELECT symbol, name, stock_id,  date
			FROM stock_price JOIN stock 
				ON stock_price.stock_id = stock.id
			WHERE rsi_14 < 30
			AND date = ?
			ORDER BY symbol
			""", (current_date,))

	elif stock_filter == "above_sma_20":
		cursor.execute("""
			SELECT symbol, name, stock_id,  date
			FROM stock_price JOIN stock 
				ON stock_price.stock_id = stock.id
			WHERE close > sma_20
			AND date = ?
			ORDER BY symbol
			""", (current_date,))

	elif stock_filter == "below_sma_20":
		cursor.execute("""
			SELECT symbol, name, stock_id,  date
			FROM stock_price JOIN stock 
				ON stock_price.stock_id = stock.id
			WHERE close < sma_20
			AND date = ?
			ORDER BY symbol
			""", (current_date,))

	else:
		cursor.execute("""
			SELECT id, symbol, name FROM stock ORDER BY symbol
			""")

	rows = cursor.fetchall()


	return templates.TemplateResponse("index.html", {'request': request, 'stocks': rows})
	#return{'title': 'Dashboard', 'stocks': rows}

@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
	connection = sqlite3.connect(config.DB_FILE)
	connection.row_factory = sqlite3.Row #This converts rows to objects

	cursor = connection.cursor()

	cursor.execute("""
		SELECT id, symbol, name FROM stock WHERE symbol = ?
		""", (symbol,))

	row = cursor.fetchone()

	# cursor.execute("""
	# 	SELECT 'date', open, high, low, close, volume
	# 	FROM stock_price JOIN stock ON stock_price.stock_id = stock.id
	# 	WHERE stock.symbol = ?
	# 	ORDER BY 'date'
	# 	""", (symbol, ))
	cursor.execute("""
		SELECT * FROM stock_price
		WHERE stock_id = ?
		ORDER BY date DESC
		""", (row['id'],))

	prices = cursor.fetchall()


	# Strategies
	cursor.execute("""
		SELECT * FROM strategy
		""")

	strategies = cursor.fetchall()

	return templates.TemplateResponse("stock_detail.html", {'request': request, 'stocks': row, 'bars': prices, 'strategies':strategies})

@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
	connection = sqlite3.connect(config.DB_FILE)

	cursor = connection.cursor()

	cursor.execute("""
		INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (?, ?)
		""", (stock_id, strategy_id))

	connection.commit()

	return RedirectResponse(url = f"/strategy/{strategy_id}", status_code = 303)


@app.get("/strategies")
def strategies(request: Request):

	connection = sqlite3.connect(config.DB_FILE)
	connection.row_factory = sqlite3.Row #This converts rows to objects

	cursor = connection.cursor()

	cursor.execute("""SELECT * FROM strategy""")

	strategies = cursor.fetchall()
	return templates.TemplateResponse("strategies.html", {'request': request, 'strategies': strategies})

@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
	connection = sqlite3.connect(config.DB_FILE)
	connection.row_factory = sqlite3.Row #This converts rows to objects

	cursor = connection.cursor()

	cursor.execute("""
		SELECT id, name FROM strategy WHERE id = ?
		""", (strategy_id,))

	strategy = cursor.fetchone()

	cursor.execute("""
		SELECT *
		FROM stock JOIN stock_strategy ON stock_strategy.stock_id = stock.id
		WHERE stock_strategy.strategy_id = ?
		""", (strategy_id,))

	stocks = cursor.fetchall()

	return templates.TemplateResponse("strategy.html", {'request': request, 'stocks': stocks, 'strategy':strategy})


@app.get("/orders")
def orders(request: Request):
	# Contact with the API
	api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)

	orders = api.list_orders(status='all')

	return templates.TemplateResponse("orders.html", {'request': request, 'orders': orders})
