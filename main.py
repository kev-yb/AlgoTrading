import sqlite3, config
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import alpaca_trade_api as tradeapi
from datetime import date

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# main page
@app.get('/')
def index(request:Request):
    stock_filter = request.query_params.get('filter', False)

    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if stock_filter == 'new_closing_highs':     # filters stocks closing on new highs
        cursor.execute('''
            SELECT * FROM (
                SELECT symbol, name, stock_id, max(close), date
                from stock_price join stock on stock.id = stock_price.stock_id
                group by stock_id
                order by symbol
            ) WHERE date = (select max(date) from stock_price)
            ''') 
    elif stock_filter == 'new_closing_lows':    # filters stock closing on new lows
        cursor.execute('''
            SELECT * FROM (
                SELECT symbol, name, stock_id, min(close), date
                from stock_price join stock on stock.id = stock_price.stock_id
                group by stock_id
                order by symbol
            ) WHERE date = (select max(date) from stock_price)
            ''')
    elif stock_filter == 'rsi_overbought':      # rsi index > 70
        cursor.execute('''
            SELECT symbol, name, stock_id, rsi_14, date
            from stock_price join stock on stock.id = stock_price.stock_id
            where rsi_14 > 70 
            and date = (select max(date) from stock_price)
            order by symbol
        ''')
    elif stock_filter == 'rsi_oversold':        # rsi index < 30
        cursor.execute('''
            SELECT symbol, name, stock_id, rsi_14, date
            from stock_price join stock on stock.id = stock_price.stock_id
            where rsi_14 < 30 
            and date = (select max(date) from stock_price)
            order by symbol
        ''')
    elif stock_filter == 'above_sma_20':      # > sma20
        cursor.execute('''
            SELECT symbol, name, stock_id, date
            from stock_price join stock on stock.id = stock_price.stock_id
            where close > sma_20
            and date = (select max(date) from stock_price)
            order by symbol
        ''')
    elif stock_filter == 'below_sma_20':        # < sma20
        cursor.execute('''
            SELECT symbol, name, stock_id, date
            from stock_price join stock on stock.id = stock_price.stock_id
            where close < sma_20
            and date = (select max(date) from stock_price)
            order by symbol
        ''')
    elif stock_filter == 'above_sma_50':      # > sma50
        cursor.execute('''
            SELECT symbol, name, stock_id, date
            from stock_price join stock on stock.id = stock_price.stock_id
            where close > sma_50
            and date = (select max(date) from stock_price)
            order by symbol
        ''')
    elif stock_filter == 'below_sma_50':        # < sma50
        cursor.execute('''
            SELECT symbol, name, stock_id, rsi_14, date
            from stock_price join stock on stock.id = stock_price.stock_id
            where close < sma_50
            and date = (select max(date) from stock_price)
            order by symbol
        ''')
    else:
        cursor.execute("SELECT symbol, name FROM stock ORDER BY symbol")

    rows = cursor.fetchall()

    # NOTE: stock could exist in stock table but not in stock_price table (e.g. stock doesn't have a price yet)
    # Error checking for this is done in .html templates
    cursor.execute('''
        SELECT symbol, close, rsi_14, sma_20, sma_50, close FROM
        stock join stock_price on stock_price.stock_id = stock.id
        where date = (select max(date) from stock_price)
    ''')

    indicator_rows = cursor.fetchall()
    indicator_values = {}

    for row in indicator_rows:
        indicator_values[row['symbol']] = row

    return templates.TemplateResponse("index.html", {'request': request, "stocks":rows, "indicator_values":indicator_values})


# shows detailed view of selected stock
@app.get("/stock/{symbol}")
def stock_detail(request: Request, symbol):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()


    cursor.execute('''
        SELECT * FROM strategy
    ''')

    strategies = cursor.fetchall()


    cursor.execute("SELECT id, symbol, name FROM stock WHERE symbol=?", (symbol,))
    row = cursor.fetchone()

    cursor.execute("SELECT * FROM stock_price WHERE stock_id=? ORDER BY date DESC", (row['id'],))
    prices = cursor.fetchall()

    return templates.TemplateResponse("stock_detail.html", {'request':request, "stock": row, "bars":prices, "strategies":strategies})


# handles post request when user applies strategy on a particular stock
@app.post("/apply_strategy")
def apply_strategy(strategy_id: int = Form(...), stock_id: int = Form(...)):
    connection = sqlite3.connect(config.DB_FILE)
    cursor = connection.cursor()

    cursor.execute('''
        INSERT INTO stock_strategy (stock_id, strategy_id) VALUES (?, ?)
    ''', (stock_id, strategy_id))

    connection.commit()

    return RedirectResponse(url=f"/strategy/{strategy_id}", status_code = 303)

# view all strategies
@app.get("/strategies")
def strategies(request: Request):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute('''
        SELECT * FROM strategy
    ''')

    strategies = cursor.fetchall()

    return templates.TemplateResponse("strategies.html", {"request":request, "strategies":strategies})

# shows list of stock that a particular strategy is applied to
@app.get("/strategy/{strategy_id}")
def strategy(request: Request, strategy_id):
    connection = sqlite3.connect(config.DB_FILE)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute('''
        SELECT id, name
        FROM strategy
        WHERE id = ?
    ''', (strategy_id,))

    strategy = cursor.fetchone()

    cursor.execute('''
        SELECT symbol, name
        FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock.id
        WHERE strategy_id = ?
    ''', (strategy_id,))

    stocks = cursor.fetchall()

    return templates.TemplateResponse("strategy.html", {"request":request, "stocks":stocks, "strategy":strategy})


# view order history
@app.get("/orders")
def orders(request: Request):
    api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url = config.BASE_URL)
    orders = api.list_orders(status='all')

    return templates.TemplateResponse("orders.html", {"request":request, "orders":orders})
