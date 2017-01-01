import requests
from .errors import AuthError, MiscError
from .utils import jsonify_recipients


def forward_message(self, message_id, to_recipients, forward_comment):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    payload = '{'
    if type(forward_comment) is not None:
        payload += '"Comment" : "' + str(forward_comment) + '",'
    if type(to_recipients) is None:
        raise MiscError('To Recipients is not defined. Can not forward message.')

    payload += '"ToRecipients" : [' + jsonify_recipients(to_recipients, 'to', True) + ']}'

    r = requests.post('https://outlook.office.com/api/v2.0/me/messages/' + message_id + '/forward',
                      headers=headers, data=payload)

    if r.status_code == 401:
        raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')


def reply(self, message_id, reply_comment, reply_all):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    payload = '{ "Comment": "' + reply_comment + '"}'
    if reply_all:
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + message_id + '/replyall'
    else:
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + message_id + '/reply'
    r = requests.post(endpoint, headers=headers,
                      data=payload)

    if r.status_code == 401:
        raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')
