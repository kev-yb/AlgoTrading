import sqlite3, config
import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import TimeFrame, TimeFrameUnit
from datetime import date
import smtplib, ssl
from utils import calculate_quantity, is_dst, get_latest_weekday
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
    SELECT id FROM strategy WHERE name = "opening_range_breakout"
''')

strategy_id = cursor.fetchone()['id']

cursor.execute('''
    SELECT symbol, name 
    FROM stock JOIN stock_strategy on stock_strategy.stock_id = stock.id
    WHERE stock_strategy.strategy_id = ?
''', (strategy_id,))

stocks = cursor.fetchall()  # retrieves all stocks with the opening_range_breakout strategy applied
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


# doesn't implement opening_range_breakdown
for symbol in symbols:
    minute_bars = api.get_bars(symbol, TimeFrame(1, TimeFrameUnit.Minute), "2024-02-28", "2024-02-28", adjustment='raw').df
    minute_bars.index = pd.to_datetime(minute_bars.index, utc=True).tz_convert(pytz.timezone('US/Eastern'))


    opening_range_mask = (minute_bars.index >= start_minute_bar) & (minute_bars.index <= end_minute_bar)
    opening_range_bars = minute_bars.loc[opening_range_mask]

    opening_range_low = opening_range_bars['low'].min()
    opening_range_high = opening_range_bars['high'].max()
    opening_range = opening_range_high - opening_range_low

    after_opening_range_mask = minute_bars.index >= end_minute_bar
    after_opening_range_bars = minute_bars.loc[after_opening_range_mask]
    after_opening_range_breakout = after_opening_range_bars[after_opening_range_bars['close'] > opening_range_high]

    if not after_opening_range_breakout.empty:
        if symbol not in existing_order_symbols:
            limit_price = after_opening_range_breakout.iloc[0]['close']

            messages.append(f"placing order for {symbol} at {limit_price}, closed above {opening_range_high}\n\n{after_opening_range_breakout.iloc[0]}\n\n")

            print(f"placing order for {symbol} at {limit_price}, closed above {opening_range_high} at {after_opening_range_breakout.iloc[0]}\n\n")

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
                        limit_price=round(limit_price+opening_range, 2)
                    ),
                    stop_loss=dict(
                        stop_price =round(limit_price-opening_range, 2)
                    )
                )
            except Exception as e:
                print(f"Could not submit order: {e}")
        else:
            print(f"Opening range breakout order already made for {symbol}. Skipped")


with smtplib.SMTP_SSL(config.EMAIL_HOST, config.EMAIL_PORT, context=context) as server:
    email_messages = f"Subject: Trade Notifications for {current_date}\n\n" + "\n\n".join(messages)
    server.login(config.EMAIL_ADDRESS, config.EMAIL_PASSWORD)
    server.sendmail(config.EMAIL_ADDRESS, config.EMAIL_ADDRESS, email_messages)




