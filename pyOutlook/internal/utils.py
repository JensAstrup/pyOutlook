import functools
import inspect
import warnings

from .errors import MiscError

token = 0


def jsonify_recipients(recipient_input, recipient_type, silent):

    json_return = ''
    if not silent:
        if recipient_type == "cc":
            json_return = '"CcRecipients":['
        elif recipient_type == "to":
            json_return = '"ToRecipients":['
        elif recipient_type == "bcc":
            json_return = '"BccRecipients":['
        else:
            raise MiscError('To or CC recipients not provided')

    if isinstance(recipient_input, list):
        recipient_input = ', '.join(recipient_input)

    recipients = recipient_input.split(',')
    for num in range(len(recipients)):
        recipients[num] = recipients[num].strip()

    for m in range(0, len(recipients)):
        if len(recipients) - m == 1:
            insert = recipients[m].replace('"', "'")
            json_return += '{ "EmailAddress": { "Address": "' + insert + '" } }'
        else:
            insert = recipients[m].replace('"', "'")
            json_return += '{ "EmailAddress": { "Address": "' + insert + '" } },'

    return json_return


def set_global_token__(access_token):
    global token
    token = access_token


def get_global_token():
    return token
