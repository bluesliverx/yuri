
import logging
import re
from datetime import datetime
from pytz import timezone, UTC
from typing import Optional
from pygerduty.v2 import ContactMethod, User
from pygerduty.v2 import PagerDuty
from slackbot.bot import listen_to
from slackbot import settings
from slackbot.dispatcher import Message
import humanize


LOGGER = logging.getLogger(__name__)
CONTACT_METHOD_EMOTICON_BY_TYPE = {
    'email_contact_method': ':email:',
    'phone_contact_method': ':slack_call:',
    # Do not show anything for push or SMS notifications, since they duplicate the phone contact
    'sms_contact_method': None,
    'push_notification_contact_method': None,
}


def _is_pagerduty_configured() -> bool:
    return settings.PAGERDUTY_TOKEN and settings.PAGERDUTY_SCHEDULE_ID


def _get_client() -> Optional[PagerDuty]:
    if not _is_pagerduty_configured():
        return None
    return PagerDuty(settings.PAGERDUTY_TOKEN)


def _get_contact_method_message(contact_method: ContactMethod, add_label: bool) -> Optional[str]:
    emoticon = CONTACT_METHOD_EMOTICON_BY_TYPE.get(contact_method.type)
    if not emoticon or (hasattr(contact_method, 'enabled') and not contact_method.enabled):
        return None
    label = ''
    if add_label:
        label = f' ({contact_method.label})'
    return f'{emoticon} {contact_method.address}{label}'


def _get_user_name(user: User) -> Optional[str]:
    if not settings.PAGERDUTY_USERNAME_EMAIL_DOMAIN:
        return None
    email_suffix = f'@{settings.PAGERDUTY_USERNAME_EMAIL_DOMAIN}'
    if not user.email.endswith(email_suffix):
        return None
    return user.email.replace(email_suffix, '')


def _get_formatted_datetime(dest_time_zone_str: str, datetime_string: str) -> str:
    dest_time_zone = timezone(dest_time_zone_str)
    parsed = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=UTC)
    parsed = parsed.replace(tzinfo=dest_time_zone)
    result = humanize.naturaldate(parsed)
    if result != 'today':
        return result
    return humanize.naturaltime(parsed - datetime.now(dest_time_zone))


@listen_to(r'who is (?:currently )?on(?:-| |)call', re.IGNORECASE)
def who_is_on_call(message: Message):
    client = _get_client()
    if not client:
        LOGGER.debug('Pager duty settings are not configured, ignoring on call request')
        return

    oncalls = client.oncalls.list(include=['users'], schedule_ids=[settings.PAGERDUTY_SCHEDULE_ID])
    current_oncall = None
    for oncall in oncalls:
        current_oncall = oncall
        break
    if not current_oncall:
        message.reply(f'No current on-call information found for schedule {settings.PAGERDUTY_SCHEDULE_ID}')
        return

    # Build up contact methods string
    contact_method_messages = []
    user_name = _get_user_name(current_oncall.user)
    if user_name:
        contact_method_messages.append(f':slack: @{user_name}')
    contact_methods = current_oncall.user.contact_methods.list(time_zone='MDT')
    for contact_method in contact_methods:
        # Only add label if there is no user name
        contact_method_message = _get_contact_method_message(contact_method, not user_name)
        if contact_method_message:
            contact_method_messages.append(contact_method_message)

    # Get formatted end time
    end_time = _get_formatted_datetime(current_oncall.user.time_zone, current_oncall.end)

    message.reply_webapi(f'{current_oncall.user.name} is currently on call', in_thread=True, blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text":
                    f'*<{current_oncall.user.html_url}|{current_oncall.user.name}>* is on call '
                    f'<{current_oncall.schedule.html_url}|until {end_time}>'
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": '\n'.join(contact_method_messages)
            }
        },
    ])
