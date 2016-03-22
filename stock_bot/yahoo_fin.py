#
#  This file is a part of Stock Bot (https://github.com/cocasema/stock_bot)
#
#  Copyright (c) 2016 cocasema
#

from datetime import date

from yahoo_finance import Share
from collections import namedtuple


class YahooFinance(object):

    STOCK_URL = 'https://finance.yahoo.com/q?s={}'
    CHART_URL = 'https://chart.finance.yahoo.com/t?s={}&lang=en-US&region=US&width=400&height=240'

    ShareInfo = namedtuple(
        'ShareInfo', 'prev_close open price change change_percent page_url chart_url')

    def __init__(self, log):
        self.log = log

    def get_share_info(self, symbol):

        share = Share(symbol)
        self.log.debug(share.data_set)

        last_trade_date = share.data_set['LastTradeDate']  # '2/12/2016'
        today = date.today()
        today = '{}/{}/{}'.format(today.month, today.day, today.year)

        if last_trade_date != today:
            self.log.info(
                'Last trade date: {} != {}'.format(last_trade_date, today))
            return None

        info = self.ShareInfo(share.data_set['PreviousClose'],
                              share.data_set['Open'],
                              share.data_set['LastTradePriceOnly'],
                              share.data_set['Change'],
                              share.data_set['PercentChange'],
                              self.STOCK_URL.format(symbol),
                              self.CHART_URL.format(symbol))
        self.log.info(info)
        return info
