#coding: UTF-8
import re
from slackbot.bot import respond_to
from slackbot.bot import listen_to


@respond_to('hello$', re.IGNORECASE)
def hello_reply(message):
    message.reply('hello sender!')


@respond_to('^reply_webapi$')
def hello_webapi(message):
    message.reply_webapi('hello there!', attachments=[{
        'fallback': 'test attachment',
        'fields': [
            {
                'title': 'test table field',
                'value': 'test table value',
                'short': True
            }
        ]
    }])


@respond_to('^reply blocks$')
def hello_blocks(message):
    message.reply_webapi('hello there!', blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "You have a new request:\n*<fakeLink.toEmployeeProfile.com|Fred Enriquez - New device request>*"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Type:*\nComputer (laptop)"
                },
                {
                    "type": "mrkdwn",
                    "text": "*When:*\nSubmitted Aut 10"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Last Update:*\nMar 10, 2015 (3 years, 5 months)"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Reason:*\nAll vowel keys aren't working."
                },
                {
                    "type": "mrkdwn",
                    "text": "*Specs:*\n\"Cheetah Pro 15\" - Fast, really fast\""
                }
            ]
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Approve"
                    },
                    "style": "primary",
                    "value": "click_me_123"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "emoji": True,
                        "text": "Deny"
                    },
                    "style": "danger",
                    "value": "click_me_123"
                }
            ]
        }
    ])


@respond_to('^reply_webapi_not_as_user$')
def hello_webapi_not_as_user(message):
    message.reply_webapi('hi!', as_user=False)


@respond_to('hello_formatting')
def hello_reply_formatting(message):
    # Format message with italic style
    message.reply('_hello_ sender!')


@listen_to('hello$')
def hello_send(message):
    message.send('hello channel!')


@listen_to('hello_decorators')
@respond_to('hello_decorators')
def hello_decorators(message):
    message.send('hello!')


@listen_to('hey!')
def hey(message):
    message.react('eggplant')


@respond_to(u'你好')
def hello_unicode_message(message):
    message.reply(u'你好!')


@listen_to('start a thread')
def start_thread(message):
    message.reply('I started a thread', in_thread=True)


@respond_to('say hi to me')
def direct_hello(message):
    message.direct_reply("Here you are")

