
import logging
from slackbot.bot import nlp_label_listen_to, nlp_label_respond_to
from slackbot.dispatcher import Message


LOGGER = logging.getLogger(__name__)


@nlp_label_listen_to(r'^test/')
def process_nlp(message: Message):
    message.reply(f'Message has a test-prefixed nlp label of "{message.nlp_label}"')


@nlp_label_respond_to(r'^ignore$')
def process_nlp(message: Message):
    message.reply('This message has a nlp label that signifies it is ignored')
