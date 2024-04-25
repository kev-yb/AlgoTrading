import config, sqlite3, csv
import pandas as pd
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta, date
import time
import pytz
import tulipy as ti
from utils import calculate_quantity, is_dst, get_latest_weekday, extrapolate_data


connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()
api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)


symbols = []
stock_ids = {} # key: stock-symbol / value: stock-id

with open('qqq.csv') as f:
    reader = csv.reader(f)
    for line in reader:
        symbols.append(line[1])

cursor.execute('''
    SELECT * FROM stock
''')
stocks = cursor.fetchall()

for stock in stocks:
    symbol = stock['symbol']
    stock_ids[symbol] = stock['id']


for symbol in symbols:
    start_date = datetime(2023, 12, 5).date()
    end_date = datetime(2024, 1, 31).date()

    minutes = api.get_bars(symbol, TimeFrame(1, TimeFrameUnit.Minute), start_date, end_date, adjustment='raw').df
    minutes.index = pd.to_datetime(minutes.index, utc=True).tz_convert(pytz.timezone('US/Eastern'))

    closes = minutes.close.values
    lower, middle, upper = ti.bbands(closes, 20, 2) # SMA-20 with STD=2
    lower = extrapolate_data(lower, len(minutes))
    middle = extrapolate_data(middle, len(minutes))
    upper = extrapolate_data(upper, len(minutes))

    minutes['lower'] = lower
    minutes['middle'] = middle
    minutes['upper'] = upper

    minutes = minutes.resample('1min').ffill()    

    for idx, row in minutes.iterrows():
        cursor.execute('''
            INSERT INTO stock_price_minute (stock_id, datetime, open, high, low, close, volume, lower, middle, upper)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (stock_ids[symbol], idx.isoformat(), row['open'], row['high'], 
              row['low'], row['close'], row['volume'], row['lower'], row['middle'], row['upper']))

   

connection.commit()
