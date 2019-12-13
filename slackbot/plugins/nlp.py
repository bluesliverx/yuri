
import logging
from slackbot.bot import nlp_label_listen_to, nlp_label_respond_to
from slackbot.dispatcher import Message
from slackbot.integrations.nlp import spacy


LOGGER = logging.getLogger(__name__)


@nlp_label_listen_to(r'^test')
def process_nlp(message: Message):
    # You don't have to process the doc with spacy again, but you can if you want to retrieve more information
    doc = spacy.get_doc(message.body['text'])
    message.reply(f'Message has a test-prefixed nlp label of "{message.nlp_label}", '
                  f'{list((token.text, token.pos_, token.dep_) for token in doc)}')


@nlp_label_respond_to(r'^ignore$')
def process_nlp(message: Message):
    message.reply('This message has a nlp label that signifies it is ignored')
