import sqlite3, config
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from datetime import date
import smtplib, ssl
from utils import is_dst, get_latest_weekday, calculate_quantity
import tulipy as ti
import pandas as pd
import pytz

'''
NOTE: run this script EVERY MINUTE via a cron job

*/1 9-16 * * 1-5 [script-path] >> trade.log 2>&1

^check crontab guru website to see what this means
''' 


# setup email messaging service
context = ssl.create_default_context()

connection = sqlite3.connect(config.DB_FILE)
connection.row_factory = sqlite3.Row
cursor = connection.cursor()

cursor.execute('''
    SELECT id FROM strategy WHERE name = "bollinger_bands"
''')

strategy_id = cursor.fetchone()['id']

cursor.execute('''
    SELECT symbol, name 
    FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock.id
    WHERE stock_strategy.strategy_id = ?
''', (strategy_id,))

stocks = cursor.fetchall()  # retrieves all stocks with the bollinger_bands strategy applied
symbols = [stock['symbol'] for stock in stocks]


current_date = get_latest_weekday(date.today())
current_date = "2024-02-28"

if is_dst():
    start_minute_bar = f"{current_date} 09:30:00-05:00"
    end_minute_bar = f"{current_date} 16:00:00-05:00"
else:
    start_minute_bar = f"{current_date} 09:30:00-04:00"
    end_minute_bar = f"{current_date} 16:00:00-04:00"


api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url = config.BASE_URL)
orders = api.list_orders(status='all', limit=500, after=f"{current_date}T09:30:00Z")
existing_order_symbols = [order.symbol for order in orders if order.status != 'canceled']

# for email notification
messages = []


for symbol in symbols:
    minute_bars = api.get_bars(symbol, TimeFrame(1, TimeFrameUnit.Minute), "2024-02-28", "2024-02-28", adjustment='raw').df
    minute_bars.index = pd.to_datetime(minute_bars.index, utc=True).tz_convert(pytz.timezone('US/Eastern'))

    market_open_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index <= end_minute_bar)
    market_open_bars = minute_bars.loc[market_open_mask]

    # wait for 20 mins after market opens to execute strategy (mean-reversion)
    if len(market_open_bars) >= 20:
        closes = market_open_bars.close.values
        lower, middle, upper = ti.bbands(closes, 20, 2) # SMA-20 with STD=2

        current_candle = market_open_bars.iloc[-1]
        previous_candle = market_open_bars.iloc[-2]

        # lower bollinger band (mean-reversion)
        if current_candle.close > lower[-1] and previous_candle.close < lower[-2]:
            print(f"{symbol} closed above lower bollinger band")
            print(current_candle)

            if symbol not in existing_order_symbols:
                limit_price = current_candle.close
                candle_range = abs(current_candle.high - current_candle.low)

                messages.append(f"Buying for {symbol} at {limit_price}\n\n")

                try:
                    api.submit_order(
                        symbol=symbol,
                        side='buy',
                        type='limit',
                        qty=calculate_quantity(limit_price),
                        time_in_force='day',
                        order_class='bracket',
                        limit_price=limit_price,
                        take_profit=dict(
                            limit_price=round(limit_price + (candle_range * 3), 2)
                        ),
                        stop_loss=dict(
                            stop_price=round(previous_candle.low, 2)
                        )
                    )
                except Exception as e:
                    print(f"Could not submit order: {e}")
            else:
                print(f"Order already made for {symbol}. Skipped")


        # upper bollinger band (mean-reversion)
        if current_candle.close < upper[-1] and previous_candle.close > upper[-2]:
            print(f"{symbol} closed below upper bollinger band")
            print(current_candle)

            if symbol not in existing_order_symbols:
                limit_price = current_candle.close
                candle_range = abs(current_candle.high - current_candle.low)

                messages.append(f"Shorting for {symbol} at {limit_price}\n\n")

                try:
                    api.submit_order(
                        symbol=symbol,
                        side='sell',
                        type='limit',
                        qty=calculate_quantity(limit_price),
                        time_in_force='day',
                        order_class='bracket',
                        limit_price=limit_price,
                        take_profit=dict(
                            limit_price=round(limit_price - (candle_range * 3), 2)
                        ),
                        stop_loss=dict(
                            stop_price=round(previous_candle.high, 2)
                        )
                    )
                except Exception as e:
                    print(f"Could not submit order: {e}")
            else:
                print(f"Order already made for {symbol}. Skipped")

        


