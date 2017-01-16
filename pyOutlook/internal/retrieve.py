import logging

import requests

from pyOutlook.core.message import clean_return_multiple, clean_return_single
from pyOutlook.internal.errors import AuthError, MiscError

log = logging.getLogger('pyOutlook')


def get_messages(self, skip):
    """

    Args:
        self:
        skip:

    Returns: List[Message]

    """
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/messages'
    if skip > 0:
        endpoint = endpoint + '/?%24skip=' + str(skip) + '0'

    log.debug('Getting messages with Headers: {}'.format(headers))

    r = requests.get(endpoint, headers=headers)

    if r.status_code == 401:
        log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
        raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    elif r.status_code > 299:
        log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
        raise MiscError('Unhandled error received from Outlook. Check logging output.')

    return clean_return_multiple(r.json())


def get_inbox(self):
    try:
        return get_messages_from_folder_name(self, 'Inbox')
    except AuthError:
        raise AuthError('x')


def get_message(self, message_id):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/messages/' + message_id, headers=headers)
    if r.status_code == 401:
        raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_single(r.json())


def get_messages_from_folder_id(self, folder_id):
    """

    Args:
        self:
        folder_id:

    Returns: List[Message]

    """
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_id + '/messages', headers=headers)
    if r.status_code == 401:
        raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())


def get_messages_from_folder_name(self, folder_name):
    """

    Args:
        self:
        folder_name:

    Returns: List[Message]

    """
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_name + '/messages', headers=headers)
    if r.status_code == 401:
        raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())
