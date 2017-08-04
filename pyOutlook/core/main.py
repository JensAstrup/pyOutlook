# Authorization and misc functions
import logging
from typing import List

import requests

from pyOutlook.core.contact import Contact
from pyOutlook.core.message import Message
from pyOutlook.core.folder import Folder
from pyOutlook.internal.utils import check_response

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

    def get_message(self, message_id):
        """Gets message matching provided id.

         the Outlook email matching the provided message_id.

        Args:
            message_id: A string for the intended message, provided by Outlook

        Returns:
            Message

        """
        r = requests.get('https://outlook.office.com/api/v2.0/me/messages/' + message_id, headers=self.headers)
        check_response(r)
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

        check_response(r)

        return Message._json_to_messages(self, r.json())

    def inbox(self):
        """ first ten messages in account's inbox.

        Returns:
            List[Message]

        """
        return self._get_messages_from_folder_name('Inbox')

    def new_email(self, body='', subject='', to=list):
        """Creates a NewMessage object.

        Keyword Args:
            body (str): The body of the email
            subject (str): The subject of the email
            to (list[Contact]): A list of recipients to email

        Returns:
            Message

        """
        return Message(self.access_token, body, subject, to)

    def send_email(self, body=None, subject=None, to=list, cc=None, bcc=None,
                   send_as=None, attachments=None):
        """Sends an email in one method using variables to set the various pieces of the email.

        Args:
            body (str): The body of the email
            subject (str): The subject of the email
            to (list): A list of :class:`Contacts <pyOutlook.core.contact.Contact>`
            cc (list): A list of :class:`Contacts <pyOutlook.core.contact.Contact>` which will be added to the
                'Carbon Copy' line
            bcc (list): A list of :class:`Contacts <pyOutlook.core.contact.Contact>` while be blindly added to the email
            send_as (Contact): A :class:`Contact <pyOutlook.core.contact.Contact>` whose email the OutlookAccount
                has access to
            attachments (list): A list of dictionaries with two parts
                [1] 'name' - a string which will become the file's name
                [2] 'bytes' - the bytes of the file.

        """
        email = Message(self.access_token, body, subject, to, cc=cc, bcc=bcc, sender=send_as)

        if attachments is not None:
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
        """ Returns a list of all folders for this account """
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/'

        r = requests.get(endpoint, headers=self.headers)

        if check_response(r):
            return Folder._json_to_folders(self, r.json())

    def get_folder_by_id(self, folder_id):
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_id

        r = requests.get(endpoint, headers=self.headers)

        check_response(r)
        return_folder = r.json()
        return Folder._json_to_folder(self, return_folder)

    def _get_messages_from_folder_name(self, folder_name):
        """ Retrieves all messages from a folder, specified by its name. This only works with "Well Known" folders,
        such as 'Inbox' or 'Drafts'.

        Args:
            folder_name (str): The name of the folder to retrieve

        Returns: A list of :class:`Folders <pyOutlook.core.folder.Folder>`

        """
        r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_name + '/messages',
                         headers=self.headers)
        check_response(r)
        return Message._json_to_messages(self, r.json())
