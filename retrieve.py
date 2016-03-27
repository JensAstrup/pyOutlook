import requests
from pyOutlook import main


class Message(object):
    def __init__(self, message_id, body, subject, sender_email, sender_name, to_recipients):
        self.id = message_id
        self.body = body
        self.subject = subject
        self.senderEmail = sender_email
        self.senderName = sender_name
        self.toRecipients = to_recipients


class Messages(object):
    def __init__(self):
        self.messages = []


def clean_return_multiple(json):
    return_list = []
    for key in json['value']:
        uid = key['Id']
        return_list.append(uid)
    return return_list


def clean_return_single(json):
    uid = json['Id']
    subject = json['Subject']
    sender_email = json['Sender']['EmailAddress']['Address']
    sender_name = json['Sender']['EmailAddress']['Name']
    body = json['Body']['Content']
    to_recipients = json['ToRecipients']
    return_message = Message(uid, body, subject, sender_email, sender_name, to_recipients)
    return return_message


def get_messages(self):
    headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
    r = requests.get('https://outlook.office.com/api/v2.0/me/messages', headers=headers)
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
    return clean_return_single(r.json())