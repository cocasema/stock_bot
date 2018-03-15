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

from retrying import retry

from cement.core.foundation import CementApp
from cement.core.exc import CaughtSignal

import slack

from yahoo_fin import YahooFinance
from google_fin import GoogleFinance
from alphav_fin import AlphaVantage

def retry_if_not_exit(exception):
    return (not isinstance(exception, KeyboardInterrupt)
        and not isinstance(exception, SystemExit)
        and not isinstance(exception, CaughtSignal))

class StockBot(CementApp):

    class Meta:
        label = 'stock_bot'

    def setup(self):
        super().setup()
        self.log.info('Setting up')

        self.test_mode = os.getenv('TEST') != None
        if self.test_mode:
            self.log.warning('Test mode')

        provider = self.config[self.Meta.label].get(
            'provider', 'alpha_vantage').lower()
        provider_options = self.config[self.Meta.label].get(
            'provider_options', '')
        provider_options = dict(item.split('=') for item in provider_options.split(';'))
        self.provider = {
            'google': GoogleFinance,
            'yahoo': YahooFinance,
            'alpha_vantage': AlphaVantage}[provider](self.log, provider_options)
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

                for message in [self.query_symbol(symbol) for symbol in symbols]:
                    if message:
                        self.slack_client.send(message)

        except (KeyboardInterrupt, SystemExit, CaughtSignal):
            raise
        except:
            self.log.error(traceback.format_exc())

        self.log_time_of_next_run()

    @retry(stop_max_attempt_number=5,
           retry_on_exception=retry_if_not_exit,
           wait_exponential_multiplier=2000,
           wait_exponential_max=15000)
    def try_get_share_info(self, symbol):
        try:
            return self.provider.get_share_info(symbol)
        except Exception as e:
            self.log.warning('Couldn\'t get info for symbol "{}" : {}'.format(symbol, e))
            raise

    def query_symbol(self, symbol):
        # if len(symbol) > 5 or not symbol.isalpha():
        #    self.log.warning('Symbol string is bad: "{}"', symbol)
        #    return
        try:
            info = self.try_get_share_info(symbol)
            if not info:
                self.log.warning('Skipping symbol "{}"'.format(symbol))
                return

            emoji = self.get_emoji(float(info.change_percent[:-1]))
            return '{}*{}*  {} -> {}  {} ({})'.format(
                emoji, symbol, info.prev_close, info.price, info.change, info.change_percent)
        except (KeyboardInterrupt, SystemExit, CaughtSignal):
            raise
        except:
            self.log.error(traceback.format_exc())
            return ':disappointed: Couldn\'t get info for symbol "{}"'.format(symbol)

    ZERO_EMOJI = ':neutral_face:'
    POS_EMOJI = [
        (+25.0, ':champagne:'),
        (+15.0, ':smiley:'),
        (+5.0, ':thinking_face:'),
        (+0.0, ':stock_up:')
    ]
    NEG_EMOJI = [
        (-25.0, ':scream:'),
        (-15.0, ':cold_sweat:'),
        (-5.0, ':fearful:'),
        (-0.0, ':stock_down:')
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
