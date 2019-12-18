
import inquirer
import json
import os
import random
import shutil
import slacker
import time
from inquirer.render.console import ConsoleRender
from inquirer.themes import GreenPassion
from requests import Session
from typing import Any, Dict, List, Optional, Set, Tuple
from . import training


parent_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))

# Use the env var path or ../yuri-data
ROOT_PATH = os.environ.get('YURI_ROOT_PATH', os.path.join(parent_path, 'yuri-data'))
DEFAULT_DATA_FILE = os.path.join(ROOT_PATH, 'slack_channel_data/data.json')
DEFAULT_MODEL_DIR = os.path.join(ROOT_PATH, 'slack_channel_model')
DEFAULT_BATCH_SIZE = 10
DIRECTION_NEWER = True
DIRECTION_OLDER = False
IGNORE_LABEL = 'ignore'
CREATE_LABEL = '+add new'
INQUIRER_RENDER = ConsoleRender(theme=GreenPassion())


def get_client(token: str, session: Optional[Session] = None) -> slacker.Slacker:
    if not token:
        raise Exception(f'No token was provided')
    if not token.startswith('xoxp-'):
        raise Exception(f'The provided token is invalid since it not a user token, please use a user token instead')
    return slacker.Slacker(token, session=session)


def get_channel_id(token: str, name: str, session: Optional[Session] = None) -> str:
    # Strip off # prefix if specified
    if name.startswith('#'):
        name = name[1:]

    client = get_client(token, session=session)
    start_query = True
    cursor = None
    while start_query or cursor:
        start_query = False
        try:
            # Query 1000 at a time (the max supported) to keep the number of requests lower
            response = client.conversations.list(types=['public_channel', 'private_channel'], cursor=cursor, limit=1000)
        except Exception as e:
            if inquirer.confirm(f'Encountered error while retrieving channel ID for {name} ({e}), retry?', default=True):
                return get_channel_id(token, name, session=session)
            raise
        channels = response.body['channels']
        for channel in channels:
            if channel['name'] == name:
                return channel['id']
        cursor = response.body.get('response_metadata', {}).get('next_cursor')
    raise Exception(f'Could not find channel {name} in list of channels for this user')


def get_messages(
        token: str, channel_id: str, start_timestamp: Optional[str], end_timestamp: Optional[str],
        direction: bool, batch_size: Optional[int], session: Optional[Session] = None
) -> Tuple[List[dict], Optional[str], Optional[str]]:
    """
    Retrieves a list of messages
    :return: Tuple of messages sorted according to the direction and the start/end timestamps
    """
    client = get_client(token, session=session)
    if direction == DIRECTION_OLDER:
        timestamp_args = {'latest': start_timestamp}
    else:
        timestamp_args = {'oldest': end_timestamp}
    try:
        response = client.conversations.history(channel_id, limit=batch_size, **timestamp_args)
    except Exception as e:
        if inquirer.confirm(f'Encountered error while retrieving messages ({e}), retry?', default=True):
            return get_messages(
                token, channel_id, start_timestamp, end_timestamp, direction, batch_size, session=session
            )
        # Return nothing since we did not retry
        return [], None, None
    # The messages are already in reverse age order, with the latest chronologically at the front of the list
    messages = response.body['messages']
    if direction == DIRECTION_OLDER:
        start_timestamp = messages[-1]['ts'] if len(messages) > 0 else None
    else:
        # If we want newer messages, reverse the order
        messages.reverse()
        end_timestamp = messages[-1]['ts'] if len(messages) > 0 else None
    return messages, start_timestamp, end_timestamp


def get_data_labels(data: Dict[str, dict]) -> Set[str]:
    """
    Retrieves all labels that have already been classified.
    :param data:
    :return:
    """
    # Always remove the ignore label
    return set(data[elem]['label'] for elem in data).difference([IGNORE_LABEL])


def print_classification_entries(classifications: Dict[str, dict]):
    for message_id, classification in classifications.items():
        print(f'Text: {classification["text"]}')
        print(f'Label: {classification["label"]}')


def get_label(existing_labels: Set[str]) -> str:
    label = inquirer.list_input(
        'Please choose a label to apply to this message',
        choices=[IGNORE_LABEL] + sorted(existing_labels) + [CREATE_LABEL],
        render=INQUIRER_RENDER
    )
    if label == CREATE_LABEL:
        label = create_label(existing_labels)
        if not label:
            return get_label(existing_labels)
        # Add new label to the set of existing labels
        existing_labels.add(label)
    return label


def create_label(existing_labels: Set[str]) -> Optional[str]:
    new_label = inquirer.text(
        message="New label name (enter CANCEL to select an existing label)", render=INQUIRER_RENDER
    )
    if new_label == 'CANCEL':
        # Return nothing to cancel
        return None
    if not new_label or new_label in existing_labels or new_label == CREATE_LABEL:
        print(f'Error: new label "{new_label}" is invalid, '
              f'it may already exist or be reserved, please try again')
        return create_label(existing_labels)
    return new_label


def classify_batch(messages: List[dict], data: Dict[str, dict], all_labels: Set[str],
                   ignore_user_ids: Optional[Set[str]] = None) -> Tuple[Dict[str, dict], Dict[str, dict]]:
    messages_len = len(messages)
    added = {}
    updated = {}
    for i, message in enumerate(messages):
        message_text = message.get('text') or '<NO TEXT>'
        message_id = f'{message.get("ts")}-{message.get("user")}'
        print(f'{i + 1}/{messages_len} {message_text}')
        # We cannot check for blocks as the newer updates of the slack client always add blocks apparently
        if not message.get('text') or message.get('attachments'):
            print('Message has no text or attachments, skipping')
            continue
        message_user = message.get('user')
        if ignore_user_ids and message_user in ignore_user_ids:
            print(f'Message is from an ignored user ID ({message_user}), skipping')
            continue

        classification = data.get(message_id)
        if classification:
            # Update classification text if it was modified
            changed = False
            if message_text != classification.get('text'):
                classification['text'] = message_text
                changed = True

            # A classification already exists for this message
            if not inquirer.confirm(f'There is already an existing classification for this message'
                                    f'{"(text has been modified)" if changed else ""}, '
                                    f'do you want to change it from {classification["label"]}?',
                                    render=INQUIRER_RENDER):
                continue

            # Copy the classification so that it can modified multiple times if there are problems
            updated[message_id] = classification.copy()
        else:
            # No classification exists, prompt to skip (classify as ignore) or add an operation for it
            classification = {
                'text': message_text,
                'label': None,
            }
            # Add to added dict
            added[message_id] = classification

        # Set classification label
        label = get_label(all_labels)
        classification['label'] = label

    print('--------------------------------------Summary----------------------------------------')
    if updated:
        print(f'Updated {len(updated)} existing classification(s):')
        print_classification_entries(updated)
    if added:
        print(f'Added {len(added)} new classification(s):')
        print_classification_entries(added)
    else:
        print('No new classification entries added')
    if not inquirer.confirm('Are the above entries correct?', default=True, render=INQUIRER_RENDER):
        return classify_batch(messages, data, all_labels, ignore_user_ids=ignore_user_ids)

    return added, updated


def classify_messages(token: str, channel_id: str, data: Dict[str, dict], start_timestamp: Optional[str],
                      end_timestamp: Optional[str], direction: bool,
                      ignore_user_ids: Optional[Set[str]], batch_size: Optional[int] = None,
                      session: Optional[Session] = None) -> Tuple[Optional[str], Optional[str]]:
    all_labels = get_data_labels(data)
    done = False
    while not done:
        print('-------------------------------------------------------------------------------------')
        previous_start_timestamp = start_timestamp
        previous_end_timestamp = end_timestamp
        messages, start_timestamp, end_timestamp = get_messages(
            token, channel_id, start_timestamp, end_timestamp, direction, batch_size, session=session
        )

        # Make sure the timestamps are actually set (if get_messages returns none for them, use the last values)
        start_timestamp = start_timestamp or previous_start_timestamp
        end_timestamp = end_timestamp or previous_end_timestamp

        # Create a timestamp label for messages
        if direction == DIRECTION_OLDER:
            timestamp_label = f'before {start_timestamp}'
        else:
            timestamp_label = f'after {end_timestamp}'

        # Make sure there are messages to process
        if not messages:
            print(f'No new messages found {timestamp_label}, exiting')
            break

        # Classify the next batch
        print(f'Retrieved new batch of {len(messages)} message{"s" if len(messages) > 1 else ""} ({timestamp_label})')
        added, updated = classify_batch(messages, data, all_labels, ignore_user_ids=ignore_user_ids)
        for message_id, classification in added.items():
            data[message_id] = classification
        for message_id, classification in updated.items():
            data[message_id] = classification

        # Continue?
        if not inquirer.confirm(f'{len(data)} total messages classified, continue to the next batch of messages?',
                                default=True, render=INQUIRER_RENDER):
            done = True

    return start_timestamp, end_timestamp


def load_data(data_file: str, append: bool = True) -> Tuple[dict, Optional[str], Optional[str]]:
    print(f'Using data file at {data_file}')
    if not os.path.exists(data_file):
        return {}, None, None

    if not append:
        raise Exception(
            f'The data file ({data_file}) exists and append is disabled, please specify another data file'
        )

    # Load existing data
    with open(data_file, 'r') as fobj:
        data_file = json.loads(fobj.read())
        if not data_file:
            raise Exception(f'The existing data file ({data_file}) is invalid, please check the file')
        data = data_file.get('data', {})
        print(f'Found {len(data)} total entries stored in the data file')
        return data, data_file.get('start_timestamp'), data_file.get('end_timestamp')


def write_data(data: Dict[str, dict], start_timestamp: Optional[str], end_timestamp: Optional[str], data_file: str):
    # Make the directory start
    dir_path = os.path.dirname(data_file)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Write out the new file
    with open(data_file, 'w') as fobj:
        fobj.write(json.dumps({
            'data': data,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
        }, indent=2))
        print(f'Successfully wrote data to {data_file}')

    # Copy the result file to a file versioned with a timestamp
    shutil.copy(data_file, f'{data_file}.{time.time()}')


def test_model(args):
    if not args.model_dir:
        raise Exception('The model dir was not specified, please try again')
    if not args.test_text_or_file:
        raise Exception('Text to test must be provided')

    print(f'Loading model from {args.model_dir}')

    has_failures = False
    if os.path.exists(args.test_text_or_file):
        print(f'Reading {args.test_text_or_file} as a tab-separated file')
        with open(args.test_text_or_file, 'r') as fobj:
            file_contents = fobj.read()
        for i, line in enumerate(file_contents.splitlines()):
            elems = line.split('\t')
            if len(elems) != 2:
                raise Exception(
                    f'Line {i + 1} of {args.test_text_or_file} is invalid, '
                    f'it should contain two tab-separated values, but has {len(elems)}'
                )
            if not training.test_textcat_model(args.model_dir, elems[0], elems[1]):
                has_failures = True
    else:
        print(f'Testing text "{args.test_text_or_file}"')
        if not training.test_textcat_model(args.model_dir, args.test_text_or_file, args.expected_label):
            has_failures = True

    if has_failures:
        raise Exception('Encountered verification errors, please see above')
    else:
        print(f'All tests passed successfully')

    
def train(args):
    if not args.output_dir:
        raise Exception('The output dir was not specified, please try again')

    data, _, _ = load_data(args.data_file)
    labels = set(data[key]['label'] for key in data)

    def get_labels(true_label: str) -> Dict[str, bool]:
        nonlocal labels
        result = {}
        for label in labels:
            result[label] = true_label == label
        return result

    def data_func() -> Tuple[
        List[Tuple[Any, Dict[str, Dict[str, bool]]]], List[Tuple[Any, Dict[str, Dict[str, bool]]]]
    ]:
        nonlocal data
        limit = len(data)
        train_limit = int(limit * (args.eval_percentage / 100))
        print(f'Training data with {train_limit} entries and evaluating with {limit - train_limit} entries '
              f'({args.eval_percentage}%)')
        tuple_data = []
        for _, classification in data.items():
            tuple_data.append(
                (classification['text'], {'cats': get_labels(classification['label'])})
            )
        # Randomize the list
        random.shuffle(tuple_data)
        return tuple_data[:train_limit], tuple_data[train_limit:]

    training.train_textcat_model(
        load_data_func=data_func, output_dir=args.output_dir, labels=labels, test_text=args.test_text
    )
    

def classify(args):
    # Parse ignore user ids from comma-separated list
    if args.ignore_user_ids:
        ignore_user_ids = set(args.ignore_user_ids.split(','))
    else:
        ignore_user_ids = None

    # with Session() as session:
    channel_id = get_channel_id(args.slack_token, args.slack_channel)
    data, start_timestamp, end_timestamp = load_data(args.data_file, args.append)
    start_timestamp, end_timestamp = classify_messages(
        args.slack_token,
        channel_id,
        data,
        # Override the timestamps to use if specified
        args.start_timestamp or start_timestamp,
        args.end_timestamp or end_timestamp,
        args.direction,
        ignore_user_ids=ignore_user_ids,
        batch_size=args.batch_size,
    )
    write_data(data, start_timestamp, end_timestamp, args.data_file)
