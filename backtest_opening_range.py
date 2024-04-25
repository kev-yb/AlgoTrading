import config
import backtrader, pandas, sqlite3
from datetime import date, datetime, time, timedelta
import matplotlib
from utils import is_dst

'''
.addstrategy() and .plot() must be turned off when optimizing strategy
'''

class OpeningRange(backtrader.Strategy):
    '''
    This strategy combines opening range breakout/breakdown
    '''
    params = dict(
        num_opening_bars=15,
    )

    def __init__(self):
        self.opening_range_low = 0
        self.opening_range_high = 0
        self.opening_range = 0
        self.breakout_transaction = False
        self.breakdown_transaction = False
        self.order = None
    
    def log(self, txt, dt=None):
        if dt is None:
            dt = self.datas[0].datetime.datetime()

        print('%s, %s' % (dt, txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        if order.status in [order.Completed]:
            order_details = f"{order.executed.price}, Cost: {order.executed.value}, Comm {order.executed.comm}"

            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order_details}")
            else:  # Sell
                self.log(f"SELL EXECUTED, Price: {order_details}")
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def next(self):
        current_bar_datetime = self.data.num2date(self.data.datetime[0])
        previous_bar_datetime = self.data.num2date(self.data.datetime[-1])

        # checks if a day has passed
        if current_bar_datetime.date() != previous_bar_datetime.date():
            self.opening_range_low = self.data.low[0]
            self.opening_range_high = self.data.high[0]
            self.breakout_transaction = False
            self.breakdown_transaction = False
        
        opening_range_start_time = time(9, 30, 0)
        dt = datetime.combine(date.today(), opening_range_start_time) + timedelta(minutes=self.p.num_opening_bars)
        opening_range_end_time = dt.time()

        if current_bar_datetime.time() >= opening_range_start_time \
            and current_bar_datetime.time() < opening_range_end_time:           
            self.opening_range_high = max(self.data.high[0], self.opening_range_high)
            self.opening_range_low = min(self.data.low[0], self.opening_range_low)
            self.opening_range = self.opening_range_high - self.opening_range_low
        else:
            if self.order:
                return
            
            # BEGIN opening-range-breakout
            if self.data.close[0] > self.opening_range_high and not self.position and not self.breakout_transaction:
                self.order = self.buy()
                self.breakout_transaction = True

            # BEGIN opening-range-breakdown
            if self.data.close[0] < self.opening_range_low and not self.position and not self.breakdown_transaction:
                self.order = self.sell()
                self.breakdown_transaction = True

            # CLOSE opening-range-breakout (PROFIT)
            if self.position and self.breakout_transaction \
                and not self.breakdown_transaction \
                and (self.data.close[0] > (self.opening_range_high + self.opening_range)):
                self.close()
                
            # CLOSE opening-range-breakout (LOSS)
            if self.position and self.breakout_transaction \
                and not self.breakdown_transaction \
                and (self.data.close[0] < (self.opening_range_high - self.opening_range)):
                self.order = self.close()

            # CLOSE opening-range-breakdown (PROFIT)
            if self.position and not self.breakout_transaction \
                and self.breakdown_transaction \
                and (self.data.close[0] < (self.opening_range_low - self.opening_range)):
                self.close()
            
            # CLOSE opening-range-breakdown (LOSS)
            if self.position and not self.breakout_transaction \
                and self.breakdown_transaction \
                and (self.data.close[0] > (self.opening_range_low + self.opening_range)):
                self.close()
          
            # liquidates position by EOD (regardless of strategy type)
            if self.position and current_bar_datetime.time() >= time(15, 45, 0):
                self.log("RUNNING OUT OF TIME - LIQUIDATING POSITION")
                self.close()

    def stop(self):
        self.log('(Num Opening Bars %2d) Ending Value %.2f' %
                 (self.params.num_opening_bars, self.broker.getvalue()))

        if self.broker.getvalue() > 130000:
            self.log("*** NOTICEABLE PROFIT ***")

        if self.broker.getvalue() < 100000:
            self.log("*** NOTICEABLE LOSS ***") 


if __name__ == '__main__':
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT(stock_id) as stock_id FROM stock_price_minute
    """)
    stocks = cursor.fetchall()


    for stock in stocks:
        print(f"== Testing {stock['stock_id']} ==")

        cerebro = backtrader.Cerebro()
        cerebro.broker.setcash(100000.0)
        cerebro.addsizer(backtrader.sizers.PercentSizer, percents=95)

        if is_dst():
            dataframe = pandas.read_sql("""
                select datetime, open, high, low, close, volume
                from stock_price_minute
                where stock_id = :stock_id
                and strftime("%H:%M:%S", datetime, '-5 hours') >= '09:30:00' 
                and strftime("%H:%M:%S", datetime, '-5 hours') < '16:00:00'
                order by datetime asc
            """, conn, params={"stock_id": stock['stock_id']}, index_col='datetime', parse_dates=['datetime'])
        else:
            dataframe = pandas.read_sql("""
                select datetime, open, high, low, close, volume
                from stock_price_minute
                where stock_id = :stock_id
                and strftime("%H:%M:%S", datetime, '-4 hours') >= '09:30:00' 
                and strftime("%H:%M:%S", datetime, '-4 hours') < '16:00:00'
                order by datetime asc
            """, conn, params={"stock_id": stock['stock_id']}, index_col='datetime', parse_dates=['datetime'])
            

        data = backtrader.feeds.PandasData(dataname=dataframe, tz='US/Eastern')

        cerebro.adddata(data)
        cerebro.addstrategy(OpeningRange)

        # strats = cerebro.optstrategy(CombinationStrategy, num_opening_bars=[15, 30, 60])

        cerebro.run()
        # cerebro.plot()
