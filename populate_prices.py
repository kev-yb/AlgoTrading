import sqlite3, config
import alpaca_trade_api as tradeapi
from datetime import date
import numpy as np
import tulipy as ti                 # does not work on python 3.8+
from collections import defaultdict
from utils import get_latest_weekday

'''
NOTE: run this script EVERY DAY via a cron job
''' 

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute('''
    SELECT id, symbol, name FROM stock
''')

rows = cursor.fetchall()

symbols = []
stock_dict = {}
stock_closes = defaultdict(list)
# current_date = get_latest_weekday(date.today())
current_date = "2024-02-28"

for row in rows:
    symbol = row['symbol']
    symbols.append(symbol)
    stock_dict[symbol] = row['id']

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url = config.BASE_URL)

# minimize API calls by chunking by size = 200
chunk_size = 200
for i in range(0, len(symbols), chunk_size):
    symbol_chunk = []
    for j in range(i, i + chunk_size):
        if j >= len(symbols) or '/' in symbols[j]:
            continue
        symbol_chunk.append(symbols[j])
    
    # date is hardcoded here for now 
    barsets = api.get_bars(symbol_chunk, tradeapi.TimeFrame.Day, "2023-12-01", "2024-02-28", adjustment="raw")

    for bar in barsets:
        print(f"Processing Ticker {bar.S}")
        stock_id = stock_dict[bar.S]
        print(bar.S, bar.t.date(), bar.o)

        # SMA & RSI calculations
        stock_closes[bar.S].append(bar.c)
        sma_20, sma_50, rsi_14 = None, None, None

        if len(stock_closes[bar.S]) >= 50 and current_date == bar.t.date().isoformat():
            sma_20 = ti.sma(np.array(stock_closes[bar.S]).astype(np.float64), period=20)[-1]
            sma_50 = ti.sma(np.array(stock_closes[bar.S]).astype(np.float64), period=50)[-1]
            rsi_14 = ti.rsi(np.array(stock_closes[bar.S]).astype(np.float64), period=14)[-1]

        

        cursor.execute('''
            INSERT INTO stock_price (stock_id, date, open, high, low, close, volume, sma_20, sma_50, rsi_14) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        ''', (stock_id, bar.t.date(), bar.o, bar.h, bar.l, bar.c, bar.v, sma_20, sma_50, rsi_14))


connection.commit() 





