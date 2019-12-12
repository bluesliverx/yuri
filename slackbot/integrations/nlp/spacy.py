
import logging
import spacy
from spacy.language import Language
from slackbot import settings
from typing import Optional


LOGGER = logging.getLogger(__name__)

_nlp = None


def is_configured() -> bool:
    return not not settings.SPACY_MODEL


def _initialize_textcat(nlp: Language) -> None:
    # Ensure that the text categorizer is added to the pipeline
    if 'textcat' not in nlp.pipe_names:
        LOGGER.info('Adding the text categorizer to the spacy nlp pipeline')

        # nlp.create_pipe works for built-ins that are registered with spaCy
        textcat = nlp.create_pipe(
            'textcat', config={'exclusive_classes': True, 'architecture': 'simple_cnn'}
        )
        nlp.add_pipe(textcat, last=True)


def _get_nlp() -> Optional[Language]:
    global _nlp
    if not is_configured():
        return None
    if not _nlp:
        LOGGER.debug(f'Loading spacy model from {settings.SPACY_MODEL}')
        _nlp = spacy.load(settings.SPACY_MODEL)
        _initialize_textcat(_nlp)
        LOGGER.info(f'Initialized spacy nlp backend from model {settings.SPACY_MODEL}')
    return _nlp


def generate_label(message_text: str) -> Optional[str]:
    if not message_text:
        return None
    nlp = _get_nlp()
    if not nlp:
        return None
    doc = nlp(message_text)
    return max(doc.cats.keys(), key=lambda cat: doc.cats[cat])


# Always pre-initialize the backend if possible
_get_nlp()
