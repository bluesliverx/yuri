
import random
import spacy
from pathlib import Path
from spacy.util import minibatch, compounding, decaying
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


def get_batches(train_data, model_type):
    """
    From https://spacy.io/usage/training#tips-batch-size
    :param train_data:
    :param model_type:
    :return:
    """
    max_batch_sizes = {"tagger": 32, "parser": 16, "ner": 16, "textcat": 64}
    max_batch_size = max_batch_sizes[model_type]
    if len(train_data) < 1000:
        max_batch_size /= 2
    if len(train_data) < 500:
        max_batch_size /= 2
    batch_size = compounding(1, max_batch_size, 1.001)
    batches = minibatch(train_data, size=batch_size)
    return batches


def _evaluate(tokenizer, textcat, data: List[Tuple[str, Dict[str, Dict[str, bool]]]]):
    docs = (tokenizer(elem[0]) for elem in data)
    tp = 0.0  # True positives
    fp = 1e-8  # False positives
    fn = 1e-8  # False negatives
    tn = 0.0  # True negatives
    for i, doc in enumerate(textcat.pipe(docs)):
        gold = data[i][1]['cats']
        # print(f'eval text: {data[i][0]}')
        for label, score in doc.cats.items():
            # print(f'\tscore for {label}: {score}')
            if label not in gold:
                continue
            if score >= 0.5 and gold[label]:
                tp += 1.0
            elif score >= 0.5 and not gold[label]:
                fp += 1.0
            elif score < 0.5 and not gold[label]:
                tn += 1
            elif score < 0.5 and gold[label]:
                fn += 1
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    if (precision + recall) == 0:
        f_score = 0.0
    else:
        f_score = 2 * (precision * recall) / (precision + recall)
    return {"textcat_p": precision, "textcat_r": recall, "textcat_f": f_score}


def test_textcat_model(model_dir: str, text: str, expected_cat: Optional[str] = None) -> bool:
    """
    Tests the given test with the expected category/label (if present).
    :return: True if the expected matched actual, false otherwise (always true when expected is unspecified)
    """
    nlp = spacy.load(model_dir)
    doc = nlp(text)
    has_failures = False
    if expected_cat:
        best_score = max(doc.cats.keys(), key=lambda key: doc.cats[key])
        if best_score == expected_cat:
            print(f'PASS: {expected_cat} ({text})')
        else:
            print(f'FAIL: expected {expected_cat}, actual {best_score} ({text})')
            has_failures = True
    else:
        for cat, score in doc.cats.items():
            print('{0:.3f}\t{1}'.format(score, cat))
    return not has_failures


def train_textcat_model(
        load_data_func: Callable[
            [], Tuple[List[Tuple[Any, Dict[str, Dict[str, bool]]]], List[Tuple[Any, Dict[str, Dict[str, bool]]]]]
        ],
        n_iter: int = 20, max_texts: int = 2000, model: Optional[str] = None,
        output_dir: str = '/tmp/model', labels: Optional[Iterable[str]] = None,
        test_text: Optional[str] = None
) -> None:
    if not labels:
        raise Exception('No labels were provided to train')
    if not output_dir:
        raise Exception('Output dir must be specified')

    if model:
        nlp = spacy.load(model)
        print(f'Loaded model "{model}"')
    else:
        nlp = spacy.blank("en")
        print('Created blank "en" model')

    # Add the text classifier to the pipeline if it doesn't exist
    if 'textcat' not in nlp.pipe_names:
        # nlp.create_pipe works for built-ins that are registered with spaCy
        textcat = nlp.create_pipe(
            'textcat', config={'exclusive_classes': True, 'architecture': 'simple_cnn'}
        )
        nlp.add_pipe(textcat, last=True)
    else:
        # Otherwise, get it, so we can add labels to it
        textcat = nlp.get_pipe('textcat')

    # Add labels to text classifier
    for label in labels:
        textcat.add_label(label)

    train_data, eval_data = load_data_func()

    print(
        "Using max {} examples ({} training, {} evaluation)".format(
            max_texts, len(train_data), len(eval_data)
        )
    )

    # We mainly have small data sets, so it's recommended to use a high dropout rate at first
    # From https://spacy.io/usage/training#tips-dropout
    dropout = decaying(0.6, 0.2, 1e-4)

    # Get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "textcat"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()
        print('Training the model...')
        print('{:^5}\t{:^5}\t{:^5}\t{:^5}'.format("LOSS", "P", "R", "F"))
        batch_sizes = compounding(4.0, 32.0, 1.001)
        for i in range(n_iter):
            losses = {}
            # batch up the examples using spaCy's minibatch
            random.shuffle(train_data)
            batches = minibatch(train_data, size=batch_sizes)
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, drop=next(dropout), losses=losses)
            with textcat.model.use_params(optimizer.averages):
                # evaluate on the dev data split off in load_data()
                scores = _evaluate(nlp.tokenizer, textcat, eval_data)
            # Print a simple table
            print(
                "{0:.3f}\t{1:.3f}\t{2:.3f}\t{3:.3f}".format(
                    losses["textcat"],
                    scores["textcat_p"],
                    scores["textcat_r"],
                    scores["textcat_f"],
                )
            )

    # Create the output dir (if it doesn't exist
    output_dir = Path(output_dir)
    if not output_dir.exists():
        output_dir.mkdir()

    # Use the averages when writing out the model
    # From https://spacy.io/usage/training#tips-param-avg
    with nlp.use_params(optimizer.averages):
        nlp.to_disk(output_dir)
    print(f'Saved model to {output_dir}')

    # test the saved model
    if test_text:
        print(f'Loading saved model from {output_dir}')
        test_textcat_model(output_dir, test_text)
