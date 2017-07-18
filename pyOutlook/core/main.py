# Authorization and misc functions
import warnings
import logging
from typing import List

import requests

from pyOutlook.core.contact import Contact
from pyOutlook.internal.errors import MiscError, AuthError
from pyOutlook.core.message import Message
from pyOutlook.core.folders import Folder

log = logging.getLogger('pyOutlook')
__all__ = ['OutlookAccount']


class OutlookAccount(object):
    """Sets up access to Outlook account for all methods & classes.

    Attributes:
        access_token: A string OAuth token from Outlook allowing access to a user's account

    """

    def __init__(self, access_token):
        self.access_token = access_token

    @property
    def headers(self):
        return {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}

    def get_message(self, message_id) -> Message:
        """Gets message matching provided id.

         the Outlook email matching the provided message_id.

        Args:
            message_id: A string for the intended message, provided by Outlook

        Returns:
            Message

        """
        r = requests.get('https://outlook.office.com/api/v2.0/me/messages/' + message_id, headers=self.headers)
        if r.status_code == 401:
            raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
        return Message._json_to_message(self, r.json())

    def get_messages(self, page=0):
        """Get first 10 messages in account, across all folders.

        Keyword Args:
            page (int): Integer representing the 'page' of results to fetch

        Returns:
            List[Message]

        """
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages'
        if page > 0:
            endpoint = endpoint + '/?%24skip=' + str(page) + '0'

        log.debug('Getting messages from endpoint: {} with Headers: {}'.format(endpoint, self.headers))

        r = requests.get(endpoint, headers=self.headers)

        if r.status_code == 401:
            log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
            raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
        elif r.status_code > 299:
            log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
            raise MiscError('Unhandled error received from Outlook. Check logging output.')

        return Message._json_to_messages(self, r.json())

    def inbox(self):
        """ first ten messages in account's inbox.

        Returns:
            List[Message]

        """
        return self._get_messages_from_folder_name('Inbox')

    def new_email(self, body='', subject='', to: List[Contact] = list):
        """Creates a NewMessage object.

        Returns:
            Message

        """
        return Message(self.access_token, body, subject, to)

    def send_email(self, body=None, subject=None, to: List[Contact] = list, cc=None, bcc=None,
                   send_as=None, attachments=list):
        """Sends an email in one method using variables to set the various pieces of the email.

        Args:
            body (str): The body of the email
            subject (str): The subject of the email
            to (list): A list of email addresses
            cc (list): A list of email addresses which will be added to the 'Carbon Copy' line
            bcc (list): A list of email addresses while be blindly added to the email
            send_as (str): A string email address which the OutlookAccount has access to
            attachments (list): A list of dictionaries with two parts
                [1] 'name' - a string which will become the file's name
                [2] 'bytes' - the bytes of the file.

        """
        email = Message(self.access_token, body, subject, to)

        for attachment in attachments:
            email.attach(attachment.get('bytes'), attachment.get('name'))

        email.send()

    def sent_messages(self):
        """ last ten sent messages.

        Returns:
            list[Message]

        """
        return self._get_messages_from_folder_name('SentItems')

    def deleted_messages(self):
        """ last ten deleted messages.

        Returns:
            list[Message]

        """
        return self._get_messages_from_folder_name('DeletedItems')

    def draft_messages(self):
        """ last ten draft messages.

        Returns:
            list[Message]

        """
        return self._get_messages_from_folder_name('Drafts')

    def get_folders(self):
        headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/'

        r = requests.get(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            return Folder._json_to_folders(self, r.json())

    def get_folder_by_id(self, folder_id):
        headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_id

        r = requests.get(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            return_folder = r.json()
            return Folder._json_to_folder(self, return_folder)

    def _get_messages_from_folder_name(self, folder_name):
        """

        Args:
            self:
            folder_name:

        Returns: List[Message]

        """
        headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
        r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_name + '/messages',
                         headers=headers)
        if r.status_code == 401:
            raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
        return Message._json_to_messages(self, r.json())
