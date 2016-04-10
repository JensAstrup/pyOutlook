# Functions used by other files, but not used directly in parent code
import requests

import main
from internal.errors import AuthError, MiscError
from internal.internalMethods import jsonify_receps, get_global_token


class Message(object):
    def __init__(self, message_id, body, subject, sender_email, sender_name, to_recipients):
        # type: (str, str, str, str, str, str) -> object
        """
        :param message_id: Unique identifier for email provided by Outlook
        :type message_id: str
        :param body: The content of the email
        :type body: str
        :param subject: The subject of the email
        :type subject: str
        :param sender_email: Email address of the sender
        :type sender_email: str
        :param sender_name: The name associated with the sender email, provided by Outlook
        :type sender_name: str
        :param to_recipients: Comma separated list of recipients
        :type to_recipients: str
        """
        self.__setattr__('message_id', message_id)
        self.__setattr__('body', body)
        self.__setattr__('subject', subject)
        self.__setattr__('senderEmail', sender_email)
        self.__setattr__('senderName', sender_name)
        self.__setattr__('toRecipients', to_recipients)

    def __str__(self):
        return self.__getattribute__('message_id')

    def __repr__(self):
        return self.__getattribute__('subject')
        
    def forward_message(self, to_recipients, forward_comment):
        """
        :param to_recipients: Comma separated string of recipient emails
        :type to_recipients: str
        :param forward_comment: A comment to include with message
        :type forward_comment: str
        """
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        payload = '{'
        if type(forward_comment) is not None:
            payload += '"Comment" : "' + str(forward_comment) + '",'
        if type(to_recipients) is None:
            raise MiscError('To Recipients is not defined. Can not forward message.')

        payload += '"ToRecipients" : [' + jsonify_receps(to_recipients, 'to', True) + ']}'

        r = requests.post('https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/forward',
                          headers=headers, data=payload)

        if r.status_code == 401:
            raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')

        else:
            print 'Message Forwarded. Received the following status code from Outlook: ',
            print r.status_code

    def reply(self, reply_comment):
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/reply'

        r = requests.post(endpoint, headers=headers, data=payload)

        if r.status_code == 401:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Replied to Message. Received the following status code from Outlook: ',
            print r.status_code

    def reply_all(self, reply_comment):
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/replyall'

        r = requests.post(endpoint, headers=headers, data=payload)

        if r.status_code == 401:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Replied to Message. Received the following status code from Outlook: ',
            print r.status_code

    def delete_message(self):
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id

        r = requests.delete(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Deleted Message. Received the following status code from Outlook: ',
            print r.status_code

    def __move_to(self, destination):
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/move'
        payload = '{ "DestinationId": "' + destination + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Moved Message to ' + destination + '. Received the following status code from Outlook: ',
            print r.status_code

    def move_to_inbox(self):
        self.__move_to('Inbox')

    def move_to_deleted(self):
        self.__move_to('DeletedItems')

    def move_to_drafts(self):
        self.__move_to('Drafts')

    def move_to(self, folder_id):
        self.__move_to(folder_id)

    def __copy_to(self, destination):
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/copy'
        payload = '{ "DestinationId": "' + destination + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Copied Message to ' + destination + '. Received the following status code from Outlook: ',
            print r.status_code
            
    def copy_to_inbox(self):
        self.__copy_to('Inbox')

    def copy_to_deleted(self):
        self.__copy_to('DeletedItems')

    def copy_to_drafts(self):
        self.__copy_to('Drafts')

    def copy_to(self, folder_id):
        self.__copy_to(folder_id)




