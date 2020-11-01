import alpaca_trade_api as tradeapi
import time
import datetime
from datetime import timedelta
from pytz import timezone
tz = timezone('EST')

import numpy as np
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

alpaca_api_key = os.getenv("ALPACA_API_KEY")
alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
base_url = 'https://paper-api.alpaca.markets'

api = tradeapi.REST(alpaca_api_key, alpaca_secret_key, base_url, api_version='v2')

import logging
logging.basicConfig(filename='./apca_algo.log', format='%(name)s - %(levelname)s - %(message)s')
logging.warning('{} logging started'.format(datetime.datetime.now().strftime("%x %X")))

def get_data_bars(symbols, rate, slow, fast):

    data = api.get_barset(symbols, rate, limit=20).df

    for x in symbols:
        data.loc[:, (x, 'fast_ema')] = data[x]['close'].rolling(window=fast).mean()
        data.loc[:, (x, 'slow_ema')] = data[x]['close'].rolling(window=slow).mean()
    return data

def get_signal_bars(symbol_list, rate, ema_slow, ema_fast):
    data = get_data_bars(symbol_list, rate, ema_slow, ema_fast)
    signals = {}
    for x in symbol_list:
        if data[x].iloc[-1]['fast_ema'] > data[x].iloc[-1]['slow_ema']: signal = 1
        else: signal = 0
        signals[x] = signal
    return signals

def time_to_open(current_time):
    if current_time.weekday() <= 4:
        d = (current_time + timedelta(days=1)).date()
    else:
        days_to_mon = 0 - current_time.weekday() + 7
        d = (current_time + timedelta(days=days_to_mon)).date()
    next_day = datetime.datetime.combine(d, datetime.time(9, 30, tzinfo=tz))
    seconds = (next_day - current_time).total_seconds()
    return seconds

def run_checker(stocklist):
    print('run_checker started')
    while True:
        # Check if Monday-Friday
        if datetime.datetime.now(tz).weekday() >= 0 and datetime.datetime.now(tz).weekday() <= 4:
            # Checks market is open
            print('Trading day')
            if datetime.datetime.now(tz).time() > datetime.time(9, 30) and datetime.datetime.now(tz).time() <= datetime.time(15, 30):
                signals = get_signal_bars(stocklist, '5Min', 20, 5)
                for signal in signals:
                    if signals[signal] == 1:
                        if signal not in [x.symbol for x in api.list_positions()]:
                            logging.warning('{} {} - {}'.format(datetime.datetime.now(tz).strftime("%x %X"), signal, signals[signal]))
                            api.submit_order(signal, 1, 'buy', 'market', 'day')
                            # print(datetime.datetime.now(tz).strftime("%x %X"), 'buying', signals[signal], signal)
                    else:
                        try:
                            api.submit_order(signal, 1, 'sell', 'market', 'day')
                            logging.warning('{} {} - {}'.format(datetime.datetime.now(tz).strftime("%x %X"), signal, signals[signal]))
                        except Exception as e:
                            # print('No sell', signal, e)
                            pass

                time.sleep(60)
            else:
                # Get time amount until open, sleep that amount
                print('Market closed ({})'.format(datetime.datetime.now(tz)))
                print('Sleeping', round(time_to_open(datetime.datetime.now(tz))/60/60, 2), 'hours')
                time.sleep(time_to_open(datetime.datetime.now(tz)))
        else:
            # If not trading day, find out how much until open, sleep that amount
            print('Market closed ({})'.format(datetime.datetime.now(tz)))
            print('Sleeping', round(time_to_open(datetime.datetime.now(tz))/60/60, 2), 'hours')
            time.sleep(time_to_open(datetime.datetime.now(tz)))

stocks = ['AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CSCO', 'CVX', 'GS', 'HD', 'HON', 'IBM', 'INTC', 'JNJ', 'KO', 'JPM', 'MCD', 'MMM', 'MRK', 'MSFT', 'NKE', 'PG', 'TRV', 'UNH', 'CRM', 'VZ', 'V', 'WBA', 'WMT', 'DIS', 'DOW']

print('test:')
print(get_data_bars(['AXP'], '5Min', 20, 5).head())

run_checker(stocks)
