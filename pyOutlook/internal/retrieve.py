import requests
from .errors import AuthError

from pyOutlook.core.message import Message


def clean_return_multiple(json):
    """
    :param json:
    :return: List of messages
    :rtype: list of Message
    """
    return_list = []
    for key in json['value']:
        if 'Sender' in key:
            uid = key['Id']
            try:
                subject = key['Subject']
            except KeyError:
                subject = 'N/A'
            try:
                sender_email = key['Sender']['EmailAddress']['Address']
            except KeyError:
                sender_email = 'N/A'
            try:
                sender_name = key['Sender']['EmailAddress']['Name']
            except KeyError:
                sender_name = 'N/A'
            try:
                body = key['Body']['Content']
            except KeyError:
                body = ''
            try:
                to_recipients = key['ToRecipients']
            except KeyError:
                to_recipients = []
            return_list.append(Message(uid, body, subject, sender_email, sender_name, to_recipients))
    return return_list


# TODO: this can be reduced to one function
def clean_return_single(json):
    uid = json['Id']
    try:
        subject = json['Subject']
    except KeyError:
        subject = ''
    try:
        sender_email = json['Sender']['EmailAddress']['Address']
    except KeyError:
        sender_email = 'N/A'
    try:
        sender_name = json['Sender']['EmailAddress']['Name']
    except KeyError:
        sender_name = 'N/A'
    try:
        body = json['Body']['Content']
    except KeyError:
        body = ''
    try:
        to_recipients = json['ToRecipients']
    except KeyError:
        to_recipients = []
    return_message = Message(uid, body, subject, sender_email, sender_name, to_recipients)
    return return_message


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
    r = requests.get(endpoint, headers=headers)
    if r.status_code == 401:
        raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())


def get_inbox(self):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/Inbox/messages', headers=headers)
    if r.status_code == 401:
        raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())


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
