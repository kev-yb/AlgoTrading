from datetime import datetime, timedelta
import pytz
import numpy as np
from scipy.interpolate import interp1d

def is_dst() -> bool:
    '''
    checks if it's daylight saving time or not.
    
    NOTE: pytz.timezone('US/Eastern') automatically detects EDT/EST depending on the date
    '''
    x = datetime(datetime.now().year, 1, 1, 0, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    y = datetime.now(pytz.timezone('US/Eastern'))

    return not (y.utcoffset() == x.utcoffset())

def get_latest_weekday(today) -> str:
    '''
    calculates the latest weekday from today (i.e. if today is sunday, it returns the date of the nearest friday)
    
    NOTE: type(today): <class 'datetime.datetime'>
    '''
    # Monday ~ Sunday = 0 ~ 6
    weekday = today.weekday()

    if weekday in (5, 6):
        days_to_subtract = weekday - 4
        latest_weekday = today - timedelta(days=days_to_subtract)
        return datetime(latest_weekday.year, latest_weekday.month, latest_weekday.day).strftime("%Y-%m-%d")
    else:
        return datetime(today.year, today.month, today.day).strftime("%Y-%m-%d")


def calculate_quantity(price) -> int:
    '''
    Calculates how much shares we could purchase given our budget per stock
    '''
    return 10000 // price

def extrapolate_data(data, length):
    '''
    Takes in an array of data and extrapolates that data to a larger length
    '''
    indices = np.arange(len(data))
    data_interp = interp1d(indices, data, kind='linear')
    new_indices = np.linspace(0, len(data) - 1, length)

    extended_data = data_interp(new_indices)
    return extended_data
