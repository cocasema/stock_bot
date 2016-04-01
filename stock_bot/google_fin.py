#
#  This file is a part of Stock Bot (https://github.com/cocasema/stock_bot)
#
#  Copyright (c) 2016 cocasema
#

from datetime import date
from urllib.request import urlopen, Request
import json
from collections import namedtuple


class GoogleFinance(object):

    STOCK_URL = 'N/A'
    CHART_URL = 'N/A'

    ShareInfo = namedtuple(
        'ShareInfo', 'prev_close open price change change_percent page_url chart_url')

    PreviousClosePrice = 'pcls_fix'
    LastTradePrice = 'l'
    LastTradeDateTime = 'lt_dts'
    Change = 'c'
    ChangePercent = 'cp'

    def __init__(self, log):
        self.log = log

    def get_share_info(self, symbol):

        url = 'http://finance.google.com/finance/info?q=' + symbol
        response = urlopen(Request(url))
        content = response.read().decode('ascii', 'ignore').strip()
        content = content[3:]  # remove '// '
        content = json.loads(content)
        quote = content[0]

        self.log.debug(quote)

        # '2015-03-03T16:02:36Z'
        last_trade_date = quote[self.LastTradeDateTime][:10]
        today = date.today()
        today = '{}-{:02}-{:02}'.format(today.year, today.month, today.day)

        if last_trade_date != today:
            self.log.info(
                'Last trade date: {} != {}'.format(last_trade_date, today))
            return None

        change = quote[self.Change]

        change_pc = ('+' if change[0] == '+' else ''
                     ) + quote[self.ChangePercent] + '%'  # 'cp' doesn't have '+'

        info = self.ShareInfo(quote[self.PreviousClosePrice],
                              'N/A',
                              quote[self.LastTradePrice],
                              change,
                              change_pc,
                              self.STOCK_URL.format(symbol),
                              self.CHART_URL.format(symbol))
        self.log.info(info)
        return info
