#!/usr/bin/env python3

#
#  This file is a part of Stock Bot (https://github.com/cocasema/stock_bot)
#
#  Copyright (c) 2016 cocasema
#

import os
import time
import traceback

import schedule

from cement.core.foundation import CementApp
from cement.core.exc import CaughtSignal

from yahoo_fin import YahooFinance
import slack


class StockBot(CementApp):

    class Meta:
        label = 'stock_bot'

    def setup(self):
        super().setup()
        self.log.info('Setting up')

        self.test_mode = os.getenv('TEST') != None
        if self.test_mode:
            self.log.warn('Test mode')

        self.yahoo_finance = YahooFinance(self.log)
        self.slack_client = slack.create(self.test_mode, self.log, self.config)

        if not self.test_mode:
            days = [
                schedule.every(1).monday,
                schedule.every(1).tuesday,
                schedule.every(1).wednesday,
                schedule.every(1).thursday,
                schedule.every(1).friday,
            ]
            time = self.config['schedule']['time']
            for day in days:
                day.at(time).do(self.update)
        else:
            schedule.every(10).seconds.do(self.update)

    def loop(self):
        if self.test_mode:
            schedule.run_all()
        else:
            self.log_time_of_next_run()
        while True:
            schedule.run_pending()
            time.sleep(60)

    def log_time_of_next_run(self):
        self.log.info(
            'Next update is scheduled to run {}'.format(schedule.next_run()))

    def update(self):
        self.log.info('Updating')

        try:
            symbols = self.slack_client.get_channel_topic()
            self.log.debug('Symbols (raw): "{}"'.format(symbols))

            delimiters = ['\r', '\n', '\t', ',', '.', ';']
            for delimiter in delimiters:
                symbols = symbols.replace(delimiter, ' ')

            if symbols:
                symbols = symbols.split(' ')
                symbols = [s.upper() for s in symbols if s]
                self.log.debug('Symbols (normalized): {}'.format(symbols))

                for symbol in symbols:
                    self.post_symbol(symbol)
        except (KeyboardInterrupt, SystemExit, CaughtSignal):
            raise
        except:
            self.log.error(traceback.format_exc())

    def post_symbol(self, symbol):
        if len(symbol) > 5 or not symbol.isalpha():
            self.log.warn('Symbol string is bad: "{}"', symbol)
            return
        try:
            info = self.yahoo_finance.get_share_info(symbol)
            start_price = float(info.prev['Close'])
            end_price = float(info.today['Close'])
            delta = 100.0 * (end_price / start_price - 1.0)
            emoji = self.get_emoji(delta)
            message = '{}*{}* {:.2f} -> {:.2f} ({:+.2f}%)'.format(
                emoji, symbol, start_price, end_price, delta)
            self.slack_client.send(message)

            # self.slack_client.send_with_image('*{}* {} -> {}'.format(symbol, info.open, info.price),
            #                            url=info.chart_url,
            #                            title='details',
            #                            title_url=info.page_url)

        except (KeyboardInterrupt, SystemExit, CaughtSignal):
            raise
        except:
            self.log.error(traceback.format_exc())
            self.slack_client.send(
                'Could\'n get info for symbol "{}"'.format(symbol))
        self.log_time_of_next_run()

    ZERO_EMOJI = ':neutral_face:'
    POS_EMOJI = [
        (+25.0, ':champagne:'),
        (+15.0, ':smiley:'),
        (+5.0, ':thinking_face:'),
        (+0.0, ':chart_with_upwards_trend:')
    ]
    NEG_EMOJI = [
        (-25.0, ':scream:'),
        (-15.0, ':cold_sweat:'),
        (-5.0, ':fearful:'),
        (-0.0, ':chart_with_downwards_trend:')
    ]

    def get_emoji(self, delta):
        if '{:.2f}'.format(delta) == '0.00':
            return self.ZERO_EMOJI

        if delta >= 0:
            for v, e in self.POS_EMOJI:
                if delta >= v:
                    return e
        else:
            for v, e in self.NEG_EMOJI:
                if delta <= v:
                    return e


with StockBot() as app:
    try:
        app.run()
        app.log.info('Starting Stock Bot')
        app.loop()
    except (KeyboardInterrupt, SystemExit, CaughtSignal):
        pass
    app.log.info('Shutting down Stock Bot')
