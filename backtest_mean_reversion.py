import config
import backtrader, pandas, sqlite3
from datetime import date, datetime, time, timedelta
import matplotlib
from backtrader.indicators import BollingerBands
from utils import is_dst

'''
.addstrategy() and .plot() must be turned off when optimizing strategy
'''

class MeanReversionStrategy(backtrader.Strategy):
    '''
    This strategy tests mean reversion (SMA-20 with STD=2)
    '''
    params = dict(
        num_opening_bars = 15,
        sma_period = 20,
        stddev = 2
    )

    def __init__(self):
        self.mean_reversion_long = False
        self.mean_reversion_short = False
        self.order = None
        self.candle_range = None
        self.prev_candle =  None
        self.limit_price = None
        self.bollinger = BollingerBands(self.datas[0].close, period=self.params.sma_period, devfactor=self.params.stddev)
    
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

        current_candle = self.data.close[0]
        prev_candle = self.data.close[-1]
        candle_range = abs(current_candle - prev_candle)

        # checks if a day has passed
        if current_bar_datetime.date() != previous_bar_datetime.date():
            self.mean_reversion_long = False
            self.mean_reversion_short = False
            self.order = None
            self.candle_range = None
            self.prev_candle =  None
            self.limit_price = None

            
        opening_range_start_time = time(9, 30, 0)
        dt = datetime.combine(date.today(), opening_range_start_time) + timedelta(minutes=self.p.num_opening_bars)
        opening_range_end_time = dt.time()

        if current_bar_datetime.time() < opening_range_end_time and self.order:
            return
                
        
        # BEGIN mean-reversion-long
        if self.data.close[0] > self.bollinger.lines.bot[0] and self.data.close[-1] < self.bollinger.lines.bot[-1]  \
            and not self.position and not self.mean_reversion_long and not self.mean_reversion_short:
            self.prev_candle = self.data.low[-1]
            self.limit_price = current_candle
            self.candle_range = abs(self.data.close[0] - self.data.close[-1])
            self.mean_reversion_long = True


            self.order = self.buy()
        
        # BEGIN mean-reversion-short
        if self.data.close[0] < self.bollinger.lines.top[0] and self.data.close[-1] > self.bollinger.lines.top[-1] \
            and not self.position and not self.mean_reversion_short and not self.mean_reversion_long:
            self.prev_candle = self.data.high[-1]
            self.limit_price = current_candle
            self.candle_range = abs(self.data.close[0] - self.data.close[-1])
            self.mean_reversion_short = True


            self.order = self.sell()
        
        # CLOSE mean-reversion-long (PROFIT)
        if self.position and self.mean_reversion_long and not self.mean_reversion_short and \
           self.data.close[0] >= (self.limit_price + 3 * self.candle_range):
            self.mean_reversion_long = False

        
            self.close()

        # CLOSE mean-reversion-long (LOSS)
        if self.position and self.mean_reversion_long and not self.mean_reversion_short and \
           self.data.close[0] <= self.prev_candle:
            self.mean_reversion_long = False


            self.close()

        # CLOSE mean-reversion-short (PROFIT)
        if self.position and self.mean_reversion_short and not self.mean_reversion_long and \
           self.data.close[0] <= (self.limit_price - 3 * self.candle_range):
            self.mean_reversion_short = False


            self.close()


        # CLOSE mean-reversion-short (LOSS)
        if self.position and self.mean_reversion_short and not self.mean_reversion_long and \
           self.data.close[0] >= self.prev_candle:
            self.mean_reversion_short = False

            self.close()

        
        # liquidates position by EOD (regardless of strategy type)
        if self.position and current_bar_datetime.time() >= time(15, 45, 0):
            self.log("RUNNING OUT OF TIME - LIQUIDATING POSITION")
            self.close()

    def stop(self):
        self.log('(Num Opening Bars %2d, SMA %2d) Ending Value %.2f' %
                 (self.params.num_opening_bars, self.params.sma_period, self.broker.getvalue()))

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
                select datetime, open, high, low, close, volume, lower, middle, upper
                from stock_price_minute
                where stock_id = :stock_id
                and strftime("%H:%M:%S", datetime, '-5 hours') >= '09:30:00' 
                and strftime("%H:%M:%S", datetime, '-5 hours') < '16:00:00'
                order by datetime asc
            """, conn, params={"stock_id": stock['stock_id']}, index_col='datetime', parse_dates=['datetime'])
        else:
            dataframe = pandas.read_sql("""
                select datetime, open, high, low, close, volume, lower, middle, upper
                from stock_price_minute
                where stock_id = :stock_id
                and strftime("%H:%M:%S", datetime, '-4 hours') >= '09:30:00' 
                and strftime("%H:%M:%S", datetime, '-4 hours') < '16:00:00'
                order by datetime asc
            """, conn, params={"stock_id": stock['stock_id']}, index_col='datetime', parse_dates=['datetime'])
            
        data = backtrader.feeds.PandasData(dataname=dataframe, tz='US/Eastern')

        cerebro.adddata(data)
        cerebro.addstrategy(MeanReversionStrategy)

        # strats = cerebro.optstrategy(MeanReversionStrategy, num_opening_bars=[15, 30, 60], sma_period=[20, 40, 60])

        cerebro.run()
        cerebro.plot()
