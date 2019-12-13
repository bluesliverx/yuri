
import logging
from oncall_slackbot.bot import nlp_label_listen_to, nlp_label_respond_to
from oncall_slackbot.dispatcher import OnCallMessage
from oncall_slackbot.integrations.nlp import spacy


LOGGER = logging.getLogger(__name__)


@nlp_label_listen_to(r'^test')
def process_nlp(message: OnCallMessage):
    # You don't have to process the doc with spacy again, but you can if you want to retrieve more information
    doc = spacy.get_doc(message.body['text'])
    message.reply(f'Message has a test-prefixed nlp label of "{message.nlp_label}", '
                  f'{list((token.text, token.pos_, token.dep_) for token in doc)}')


@nlp_label_respond_to(r'^ignore$')
def process_nlp(message: OnCallMessage):
    message.reply('This message has a nlp label that signifies it is ignored')
