# -*- coding: utf-8 -*-

import logging

import slacker_blocks
from slackbot import slackclient

logger = logging.getLogger(__name__)


class BlocksSlackClient(slackclient.SlackClient):
    """
    Overrides to support blocks in calls.
    """

    def __init__(self, token, timeout=None, bot_icon=None, bot_emoji=None, connect=True):
        super(BlocksSlackClient, self).__init__(
            # Never connect since we'll do that here
            token, timeout=timeout, bot_icon=bot_icon, bot_emoji=bot_emoji, connect=False
        )
        # Replace the webapi with the blocks-supporting version
        if timeout is None:
            self.webapi = slacker_blocks.Slacker(self.token)
        else:
            self.webapi = slacker_blocks.Slacker(self.token, timeout=timeout)

        if connect:
            self.rtm_connect()

    def send_message(self, channel, message, attachments=None, blocks=None, as_user=True, thread_ts=None):
        self.webapi.chat.post_message(
                channel,
                message,
                username=self.login_data['self']['name'],
                icon_url=self.bot_icon,
                icon_emoji=self.bot_emoji,
                attachments=attachments,
                blocks=blocks,
                as_user=as_user,
                thread_ts=thread_ts)
