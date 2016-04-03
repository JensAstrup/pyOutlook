import requests
import main
from internal_methods import Message


class Messages(object):
    def __init__(self):
        self.messages = []


def clean_return_multiple(json):
    return_list = []
    for key in json['value']:
        uid = key['Id']
        return_list.append(uid)
    return return_list


def clean_return_single(self, json):
    uid = json['Id']
    subject = json['Subject']
    sender_email = json['Sender']['EmailAddress']['Address']
    sender_name = json['Sender']['EmailAddress']['Name']
    body = json['Body']['Content']
    to_recipients = json['ToRecipients']
    return_message = Message(self, uid, body, subject, sender_email, sender_name, to_recipients)
    return return_message


def get_messages(self, skip):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/messages'
    if skip > 0:
        endpoint = endpoint + '/?%24skip=' + str(skip) + '0'
    r = requests.get(endpoint, headers=headers)
    if r.status_code == 401:
        raise main.AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())


def get_inbox(self):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/Inbox/messages', headers=headers)
    if r.status_code == 401:
        raise main.AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())


def get_message(self, message_id):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/messages/' + message_id, headers=headers)
    if r.status_code == 401:
        raise main.AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_single(self, r.json())


def get_messages_from_folder_id(self, folder_id):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_id + '/messages', headers=headers)
    if r.status_code == 401:
        raise main.AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())


def get_messages_from_folder_name(self, folder_name):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_name + '/messages', headers=headers)
    if r.status_code == 401:
        raise main.AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
    return clean_return_multiple(r.json())