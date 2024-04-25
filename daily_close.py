import alpaca_trade_api as tradeapi
import config

'''
crontab:
30 12 * * 1 5 [script.path] >> trade.log 2>&1
'''

api = tradeapi.REST(config.API_KEY, config.SECRET_KEY, base_url=config.BASE_URL)

response = api.close_all_positions()

