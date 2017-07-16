# Authorization and misc functions
import warnings
import logging

import requests

from pyOutlook.internal.errors import MiscError, AuthError
from pyOutlook.internal.createMessage import NewMessage
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

    def get_message(self, message_id) -> Message:
        """Gets message matching provided id.

         the Outlook email matching the provided message_id.

        Args:
            message_id: A string for the intended message, provided by Outlook

        Returns:
            Message

        """
        headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
        r = requests.get('https://outlook.office.com/api/v2.0/me/messages/' + message_id, headers=headers)
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
        headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages'
        if page > 0:
            endpoint = endpoint + '/?%24skip=' + str(page) + '0'

        log.debug('Getting messages with Headers: {}'.format(headers))

        r = requests.get(endpoint, headers=headers)

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

    def new_email(self):
        """Creates a NewMessage object.

        Returns:
            NewMessage

        """
        return NewMessage(self.access_token)

    def send_email(self, body=None, subject=None, to=None, cc=None, bcc=None,
                   send_as=None, attachment=None):
        """Sends an email in one method using variables to set the various pieces of the email.

        Args:
            body (str): The body of the email
            subject (str): The subject of the email
            to (list): A list of email addresses
            cc (list): A list of email addresses which will be added to the 'Carbon Copy' line
            bcc (list): A list of email addresses while be blindly added to the email
            send_as (str): A string email address which the OutlookAccount has access to
            attachment (dict): A dictionary with three parts [1] 'name' - a string which will become the file's name \
            [2] 'ext' - a string which will become the file extension [3] 'bytes' - the bytes of the file.

        """
        email = NewMessage(self.access_token)
        if body is not None:
            email.set_body(body)
        if subject is not None:
            email.set_subject(subject)
        if to is not None:
            email.to(to)
        if cc is not None:
            email.cc(cc)
        if bcc is not None:
            email.bcc(bcc)
        if send_as is not None:
            email.send_as(send_as)
        if attachment is not None:
            if 'bytes' not in attachment or 'name' not in attachment or 'ext' not in attachment:
                raise TypeError('Was unable to find one or more keys in the attachment dictionary: bytes, name, ext.')
            email.attach(attachment['bytes'], attachment['name'], attachment['ext'])
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
