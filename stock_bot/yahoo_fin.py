#
#  This file is a part of Stock Bot (https://github.com/cocasema/stock_bot)
#
#  Copyright (c) 2016 cocasema
#

from datetime import date, timedelta

from yahoo_finance import Share
from collections import namedtuple


class YahooFinance(object):

    STOCK_URL = 'https://finance.yahoo.com/q?s={}'
    CHART_URL = 'https://chart.finance.yahoo.com/t?s={}&lang=en-US&region=US&width=400&height=240'

    ShareInfo = namedtuple('ShareInfo', 'today prev page_url chart_url')

    def __init__(self, log):
        self.log = log

    def get_share_info(self, symbol):
        today = date.today()
        # hopefully we can capture previous trade day here :)
        start_date = today - timedelta(10)

        self.log.debug(
            'Getting info for "{}" [{} - {}]'.format(symbol, start_date.isoformat(), today.isoformat()))

        share = Share(symbol)
        hist = share.get_historical(start_date.isoformat(), today.isoformat())
        self.log.info(hist)

        info = self.ShareInfo(hist[0], hist[1],
                              self.STOCK_URL.format(symbol),
                              self.CHART_URL.format(symbol))
        self.log.info(info)
        return info
