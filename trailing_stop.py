import config
import alpaca_trade_api as tradeapi
from utils import calculate_quantity
import tulipy as ti

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)

# symbols = ['SPY', 'IWM', 'DIA']

# for symbol in symbols:
#     quote = api.get_latest_quote(symbol)
#     print(quote)

#     api.submit_order(
#         symbol=symbol,
#         side='buy',
#         type='market',
#         qty=calculate_quantity(quote.bp),
#         time_in_force='day'
#     )

#     # orders = api.list_orders()
#     # positions = api.list_positions()

#     api.submit_order(
#         symbol=symbol,
#         side='sell'
#         type='trailing_stop',
#         qty=5,
#         time_in_force='day',
#         trail_price='5'         # can choose trail_percent (might not want it to be too low since it could bounce up)
#     )

