[Yuri the trainer who trains](https://youtu.be/1daKtciMLiE?t=38) was written
to easily train a text categorization model based on messages in an existing
slack channel. Yuri is written completely in Python 3+.

This project was built during Adobe "Garage Week" 2019 in order to support the easy creation of
bots for on-call Slack channels that listen to events and can respond intelligently. See
[bluesliverx/oncall-slackbot](https://github.com/bluesliverx/oncall-slackbot) for more
information.

## Features

* Connects to Slack via the API to download and classify or categorize messages
* Converts classified data into a [spaCy](https://spacy.io) training model
* Able to test the trained model for use in CI/CD pipelines

## Usage

### Choose your slack channel

For an existing slack channel, just make sure your user is a member of it.

For testing/demo purposes, it may be simplest to create a new slack channel and
then invite your bot or user into it. Add some messages that can be grouped
into categories (e.g. test/1, test/2, etc).

```
# Do not use the # prefix here as it is assumed
export SLACK_CHANNEL=my-slack-channel
```

### Generate a Slack API token

First, generate a Slack API token for *a real user*. Bot API tokens may not
be used as yuri uses endpoints that require user privileges such as
reading message history. This can be done on the
[Slack web API page](https://api.slack.com/web).

```
export SLACK_TOKEN=my-slack-token
```

### Create yuri data directory

```
mkdir -p yuri-data
export YURI_ROOT_PATH=`pwd`/yuri-data
```

### Classify slack messages

```
docker run -it -v $YURI_ROOT_PATH:/yuri-data -e SLACK_TOKEN bksaville/yuri classify $SLACK_CHANNEL
```

This command queries the channel `#my-channel-name` with your user token and
start at the latest message and allow you to classify each message. The data is
then saved into a custom format JSON file, by default located within this
repository. The location of the data file and the direction used to query (i.e.
earlier messages or the most recent messages) may be customized by command line
parameters passed to the script.

NOTE: Try to make sure to have 10s (or better, 100s) of messages for each
category in order to train your model correctly. During testing, it is
sufficient to have only a few messages for each category.

### Train the model

```
docker run -v $YURI_ROOT_PATH:/yuri-data bksaville/yuri train
```

This command takes the data created by the classify command, trains a spaCy
model, and outputs it into a directory in the local repository by default. Yuri
defaults to using 80% of your classified data for training and 20% for
evaluation purposes. Again, any defaults may be changed via command line
parameters.

### Test the model

```
# Displays the score of each label for the given text
docker run -v $YURI_ROOT_PATH:/yuri-data bksaville/yuri test "<my-test-text>"
# Asserts that the expected label matches the label with the best score
docker run -v $YURI_ROOT_PATH:/yuri-data bksaville/yuri test "<my-test-text>" -e "<expected-label>"
# Asserts that the label given for the text and expected label in the file match (tab-separated)
# Make sure that any files to test are mounted to a directory in the container
#   here the current directory is mounted to /source and the file is loaded from there in the container
docker run -v $YURI_ROOT_PATH:/yuri-data -v `pwd`:/source bksaville/yuri test -f /source/<my-test-file.tsv>
```

Testing the model is easy since it just involves passing test on the command line or a file
used to test expectations vs actual labels generated from the model.

Each line of the test file should look like "TEXT\tEXPECTED_LABEL". Comments are supported.

