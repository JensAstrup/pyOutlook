import logging

import requests

from pyOutlook.internal.errors import AuthError, MiscError

log = logging.getLogger('pyOutlook')





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
    return json_to_message(r.json())


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



