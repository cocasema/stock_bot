#
#  This file is a part of Stock Bot (https://github.com/cocasema/stock_bot)
#
#  Copyright (c) 2016 cocasema
#

import slacker


def create(test_mode, log, config):
    return Slack(log, config) if not test_mode else Dummy(log, config)


class Slack(object):

    SECTION = 'slack'
    SKIP_PARAMS = set(['api_token'])
    CONFIG_PARAMS = set(['channel', 'text', 'username', 'as_user', 'parse', 'link_names',
                         'unfurl_links', 'unfurl_media', 'icon_url', 'icon_emoji', 'mrkdwn'])

    def __init__(self, log, config):
        self.log = log

        assert config.has_section(
            self.SECTION), 'Missing configuration section "{}"'.format(self.SECTION)
        cfg_section = config[self.SECTION]

        self.client = slacker.Slacker(cfg_section['api_token'])
        self.channel_id = self.client.channels.get_channel_id(
            cfg_section['channel'][1:])

        self.config_params = {}
        for key in config.keys(self.SECTION):
            if not key in self.CONFIG_PARAMS:
                if not key in self.SKIP_PARAMS:
                    self.log.warn(
                        'Unknown configuraion parameter "{}.{}"'.format(self.SECTION, key))
                continue
            self.config_params[key] = cfg_section[key]
        self.log.debug('Slack params: {}'.format(self.config_params))

    def get_channel_topic(self):
        info = self.client.channels.info(self.channel_id).body
        self.log.debug(info)
        return info['channel']['topic']['value']

    def send_with_image(self, message, url, title, title_url):
        attachment = {'title': title,
                      'title_link': title_url,
                      'image_url': url,
                      'fallback': 'image'
                      }
        self.send(message, attachment)

    def send(self, message, attachment=None):
        self.log.debug('Sending message to Slack')

        params = self.config_params.copy()
        params['text'] = message

        attachments = [attachment] if attachment else []
        self.client.chat.post_message(attachments=attachments, **params)


class Dummy(object):

    def __init__(self, log, config):
        self.log = log

    def get_channel_topic(self):
        return 'goog,VMW\nMSFT'

    def send_with_image(self, message, url, title, title_url):
        self.log.debug('Not sending message to Slack: "{}, {}, {}, {}"'.format(
            message, url, title, title_url))

    def send(self, message, attachment=None):
        self.log.debug('Not sending message to Slack: "{}"'.format(message))
