A base for an on-call chat bot for [Slack](https://slack.com) and extends classes from
[lins05/slackbot](https://github.com/lins05/slackbot). While slackbot supports Python 2 and 3,
this repository is Python 3+ only.

This project was built during Adobe "Garage Week" 2019 in order to support the easy creation of
bots for on-call Slack channels that listen to events and can respond intelligently.

## Features

* [PagerDuty](https://www.pagerduty.com/) integration for querying on call information
* Natural language processing (NLP) support for smarter bots using [spaCy](https://spacy.io)
  * Currently only supports text categorization for message routing, but could support more in the future
* Supports Slack blocks in addition to attachments

## Usage

### Generate the slack api token

First you need to get the slack api token for your bot. You have two options:

1. If you use a [bot user integration](https://api.slack.com/bot-users) of slack, you can get the api token on the integration page.
2. If you use a real slack user, you can generate an api token on [slack web api page](https://api.slack.com/web).

### Perform lins05 setup

Follow the setup steps in the [lins05/slackbot](https://github.com/lins05/slackbot) repository.

### Configure PagerDuty integration

slackbot_settings.py:

```
PAGERDUTY_TOKEN = 'mytoken'
PAGERDUTY_SCHEDULE_ID = 'ABCDEFG'
PAGERDUTY_USERNAME_EMAIL_DOMAIN = 'adobe.com'
```

See the `slackbot/plugins/oncall.py` file for examples of using the PagerDuty integration.

### Configure spaCy integration

Before spaCy can be used, it must have a model trained for text categorization or text labels.
Please note that message routing is currently only capable based on labels and not any other
spaCy document properties.

#### Training a spaCy model

If you already have a spaCy textcat model to use, you may skip this section completely.

[Yuri the trainer who trains](https://youtu.be/1daKtciMLiE?t=38)
(`scripts/yuri`) can help you to easily train a text categorization model based on messages
in an existing slack channel.

##### Choose your slack channel

For an existing slack channel, just make sure your user is a member of it.

For testing, it may be simplest to create a new slack channel and then invite your bot or user
into it. Add some messages that can be grouped into categories (e.g. test/1, test/2, etc).

##### Classify slack messages

```
# NOTE: This MUST be a user token that has the ability to read channels and conversations history
# A bot token is not allowed to read conversation history and therefore cannot be used
export SLACK_TOKEN=myusertoken
scripts/yuri classify my-channel-name
```

This command query the channel `#my-channel-name` with your user token and start at the latest message
and allow you to classify each message. The data is then saved into a custom format JSON file, by
default located within this repository. The location of the data file and the direction used
to query (i.e. earlier messages or the most recent messages) may be customized by command line
parameters passed to the script.

NOTE: Try to make sure to have 10s (or better, 100s) of messages for each category in order to 
train your model correctly. During testing, it is sufficient to have only a few messages for 
each category. To use the sample `nlp.py` plugin provided in this repository, be sure to have at 
least one category/label that starts with "test".

##### Train the model

```
scripts/yuri train
```

This command takes the data created by the classify command, trains a spaCy model, and outputs it
into a directory in the local repository by default. Yuri defaults to using 80% of your classified
data for training and 20% for evaluation purposes. Again, any defaults may be changed via command
line parameters.

##### Test the model

```
# Displays the score of each label for the given text
scripts/yuri test <my-test-text>
# Asserts that the expected label matches the label with the best score
scripts/yuri test <my-test-text> -e <expected-label>
# Asserts that the label given for the text and expected label in the file match (tab-separated)
scripts/yuri test <my-test-file.tsv>
```

Testing the model is easy since it just involves passing test on the command line or a file
used to test expectations vs actual labels generated from the model.

#### Configure spaCy model location

slackbot_settings.py:

```
SPACY_MODEL = '/model/dir'
```

This is the same directory that was generated using yuri or by manually training a spaCy model.

#### Use nlp responders in your plugins

See the `slackbot/plugins/nlp.py` file for examples of using NLP in your plugins.