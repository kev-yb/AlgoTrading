# Full stack stock trading application
<br>
<u>Technologies:</u> Python, Alpaca Trading API, FASTAPI, SQLite3, Pandas, NumPy, SciPy<br>
+ A full stack stock trading application that applies various trading strategies (opening-range-breakout, opening-range-breakdown, mean-inversion) on US stocks
+ Allows filtering of stocks based on their RSI and SMA values to help users shortlist stocks based on their desired trading strategies
+ Time data are converted from UTC values provided by Alpaca Trading API to EST/EDT
+ Stocks are automatically liquidated before the market closes if a position is left opened since this is a day trading application and the consequences of leaving a position open while the market is closed hasn't been investigated yet.
+ Uses SMTP to send email notifications when a trade has been made
+ Uses the Backtrader library to allow users to test (a combination of) strategies over a set of data supplied to Cerebro.


<u>Note:</u> Python 3.7+ is required to run the application due to tulipy dependencies


**Home Page**
<img width="1512" alt="Screenshot 2024-05-19 at 9 44 51 PM" src="https://github.com/kev-yb/AlgoTrading/assets/76458258/081ddc20-435b-4d52-b3f5-c41fc53d9ffd"><br><br><br>


**Filters (New Closing Highs/Lows, RSI (Relative Strength Index), SMA (Simple Moving Average))**
<img width="1076" alt="Screenshot 2024-05-19 at 9 47 26 PM" src="https://github.com/kev-yb/AlgoTrading/assets/76458258/fdcedec8-e12d-49ea-b04e-79a04a38ecf1"><br><br><br>


**Stock Details (Price History Table + Apply Strategy Dropdown)**
<img width="1512" alt="Screenshot 2024-05-19 at 9 52 00 PM" src="https://github.com/kev-yb/AlgoTrading/assets/76458258/75beab39-7d0b-4ef5-8bc1-ceab158dd7bf">
<img width="1216" alt="Screenshot 2024-05-19 at 9 51 29 PM" src="https://github.com/kev-yb/AlgoTrading/assets/76458258/fe9bbc37-d5b2-4d06-a2d6-b60ad962ab7f"><br><br><br>


**Backtesting Mean Inversion + Opening Range Breakout/Breakdown (with Backtrader)**
Example: Backtesting on MSFT (Microsoft) minute data over the span of 60 days<br>

Log Messages
<img width="668" alt="Screenshot 2024-05-19 at 10 01 45 PM" src="https://github.com/kev-yb/AlgoTrading/assets/76458258/ac132d50-a490-4120-98e7-29bc4b0249e0">
<img width="766" alt="Screenshot 2024-05-19 at 10 02 19 PM" src="https://github.com/kev-yb/AlgoTrading/assets/76458258/93ebfa3c-0f1f-488a-9169-30cc23af0481"><br><br><br>

Backtrader Plot on Matplotlib (Tracks buy/sell positions)
<img width="1473" alt="Screenshot 2024-05-19 at 10 05 00 PM" src="https://github.com/kev-yb/AlgoTrading/assets/76458258/c5062365-4174-4639-adfc-e93ddaddc0c0">




