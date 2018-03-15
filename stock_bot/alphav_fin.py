#
#  This file is a part of Stock Bot (https://github.com/cocasema/stock_bot)
#
#  Copyright (c) 2017 cocasema
#

import pprint
from datetime import date

from alpha_vantage.timeseries import TimeSeries
from collections import namedtuple


class AlphaVantage(object):

    STOCK_URL = 'N/A'
    CHART_URL = 'N/A'

    ShareInfo = namedtuple(
        'ShareInfo', 'prev_close open price change change_percent page_url chart_url')

    def __init__(self, log, options=None):
        self.log = log
        self.ts = TimeSeries(key=options['key'])

    def get_share_info(self, symbol):
        data, meta_data = self.ts.get_daily(symbol)

        last_trade_date = meta_data['3. Last Refreshed'].split()[0]  # '2018-03-14 15:10:45'
        today = date.today().isoformat()

        if last_trade_date != today:
            self.log.info(
                'Last trade date: {} != {}'.format(last_trade_date, today))
            return None

        date_prev = sorted(data.keys())[-2]
        data_prev = data[date_prev]

        data_today = data[today]

        prev_close = float(data_prev['4. close'])
        today_open = float(data_today['1. open'])
        today_close = float(data_today['4. close'])

        change = today_close - prev_close
        change_str = '{0:+.2f}'.format(change)
        change_pc = '{0:+.2f}%'.format(100.0 * change / prev_close)

        info = self.ShareInfo(prev_close,
                              today_open,
                              today_close,
                              change_str,
                              change_pc,
                              self.STOCK_URL.format(symbol),
                              self.CHART_URL.format(symbol))
        self.log.info(info)
        return info
