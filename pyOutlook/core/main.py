# Authorization and misc functions
import json
import logging

from datetime import datetime

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
        self.access_token = access_token  # type: str
        self._auto_reply = None  # type: str
        self._contact_overrides = None

    @property
    def _headers(self):
        return {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}

    @property
    def auto_reply_message(self):
        """ The account's Internal auto reply message. Setting the value will change the auto reply message of the
         account, automatically setting the status to enabled (but not altering the schedule). """
        if self._auto_reply is None:
            r = requests.get('https://outlook.office.com/api/v2.0/me/MailboxSettings/AutomaticRepliesSetting',
                             headers=self._headers)
            check_response(r)
            self._auto_reply = r.json().get('InternalReplyMessage')

        return self._auto_reply

    @auto_reply_message.setter
    def auto_reply_message(self, value):
        self.set_auto_reply(value)

    @property
    def contact_overrides(self):
        endpoint = 'https://outlook.office.com/api/v2.0/me/InferenceClassification/Overrides'

        if self._contact_overrides is None:
            r = requests.get(endpoint, headers=self._headers)

            check_response(r)

            self._contact_overrides = Contact._json_to_contacts(r.json())

        return self._contact_overrides

    class AutoReplyAudience(object):
        INTERNAL_ONLY = 'None'
        CONTACTS_ONLY = 'ContactsOnly'
        ALL = 'All'

    class AutoReplyStatus(object):
        DISABLED = 'Disabled'
        ALWAYS_ENABLED = 'AlwaysEnabled'
        SCHEDULED = 'Scheduled'

    def set_auto_reply(self, message, status=AutoReplyStatus.ALWAYS_ENABLED, start=None, end=None,
                       external_message=None, audience=AutoReplyAudience.ALL):
        # type: (str, OutlookAccount.AutoReplyStatus, datetime, datetime, str, OutlookAccount.AutoReplyAudience) -> None
        """ Set an automatic reply for the account.
        Args:
            message (str): The message to be sent in replies. If external_message is provided this is the message sent
            to internal recipients
            status (OutlookAccount.AutoReplyStatus): Whether the auto-reply should be always enabled, scheduled, or
            disabled. You can use :class:`AutoReplyStatus <pyOutlook.core.main.OutlookAccount.AutoReplyStatus>` to
            provide the value. Defaults to ALWAYS_ENABLED.
            start (datetime): If status is set to SCHEDULED, this is when the replies will start being sent.
            end (datetime): If status is set to SCHEDULED, this is when the replies will stop being sent.
            external_message (str): If provided, this message will be sent to external recipients.
            audience (OutlookAccount.AutoReplyAudience): Whether replies should be sent to everyone, contacts only,
            or internal recipients only. You can use
            :class:`AutoReplyAudience <pyOutlook.core.main.OutlookAccount.AutoReplyAudience>` to provide the value.

        """

        start_is_none = start is None
        end_is_none = end is None

        if (not start_is_none and end_is_none) or (start_is_none and not end_is_none):
            raise ValueError('Start and End must both either be None or datetimes')

        start_is_datetime = isinstance(start, datetime)
        end_is_datetime = isinstance(end, datetime)

        if not start_is_datetime and not start_is_none or not end_is_datetime and not end_is_none:
            raise ValueError('Start and End must both either be None or datetimes')

        request_data = dict(Status=status, ExternalAudience=audience)

        # Outlook requires both an internal and external message. For convenience, pyOutlook allows only one message
        # and uses that as the external message if none is provided
        if external_message is None:
            external_message = message

        request_data.update(InternalReplyMessage=message, ExternalReplyMessage=external_message)

        if not start_is_none and not end_is_none:
            request_data.update(ScheduledStartDateTime=dict(DateTime=str(start)))
            request_data.update(ScheduledEndDateTime=dict(DateTime=str(end)))

        data = {
            "@odata.context": "https://outlook.office.com/api/v2.0/$metadata#Me/MailboxSettings",
            "AutomaticRepliesSetting": request_data
        }

        requests.patch('https://outlook.office.com/api/v2.0/me/MailboxSettings',
                       headers=self._headers, data=json.dumps(data))

        self._auto_reply = message

    def get_message(self, message_id):
        """Gets message matching provided id.

         the Outlook email matching the provided message_id.

        Args:
            message_id: A string for the intended message, provided by Outlook

        Returns:
            :class:`Message <pyOutlook.core.message.Message>`

        """
        r = requests.get('https://outlook.office.com/api/v2.0/me/messages/' + message_id, headers=self._headers)
        check_response(r)
        return Message._json_to_message(self, r.json())

    def get_messages(self, page=0):
        """Get first 10 messages in account, across all folders.

        Keyword Args:
            page (int): Integer representing the 'page' of results to fetch

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>`]

        """
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages'
        if page > 0:
            endpoint = endpoint + '/?%24skip=' + str(page) + '0'

        log.debug('Getting messages from endpoint: {} with Headers: {}'.format(endpoint, self._headers))

        r = requests.get(endpoint, headers=self._headers)

        check_response(r)

        return Message._json_to_messages(self, r.json())

    def inbox(self):
        """ first ten messages in account's inbox.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>`]

        """
        return self._get_messages_from_folder_name('Inbox')

    def new_email(self, body='', subject='', to=list):
        """Creates a :class:`Message <pyOutlook.core.message.Message>` object.

        Keyword Args:
            body (str): The body of the email
            subject (str): The subject of the email
            to (List[Contact]): A list of recipients to email

        Returns:
            :class:`Message <pyOutlook.core.message.Message>`

        """
        return Message(self, body, subject, to)

    def send_email(self, body=None, subject=None, to=list, cc=None, bcc=None,
                   send_as=None, attachments=None):
        """Sends an email in one method, a shortcut for creating an instance of
        :class:`Message <pyOutlook.core.message.Message>` .

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
        email = Message(self, body, subject, to, cc=cc, bcc=bcc, sender=send_as,)

        if attachments is not None:
            for attachment in attachments:
                email.attach(attachment.get('bytes'), attachment.get('name'))

        email.send()

    def sent_messages(self):
        """ last ten sent messages.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>`]

        """
        return self._get_messages_from_folder_name('SentItems')

    def deleted_messages(self):
        """ last ten deleted messages.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>` ]

        """
        return self._get_messages_from_folder_name('DeletedItems')

    def draft_messages(self):
        """ last ten draft messages.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>`]

        """
        return self._get_messages_from_folder_name('Drafts')

    def get_folders(self):
        """ Returns a list of all folders for this account

            Returns:
                List[:class:`Folder <pyOutlook.core.folder.Folder>`]
        """
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/'

        r = requests.get(endpoint, headers=self._headers)

        if check_response(r):
            return Folder._json_to_folders(self, r.json())

    def get_folder_by_id(self, folder_id):
        """ Retrieve a Folder by its Outlook ID

        Args:
            folder_id: The ID of the :class:`Folder <pyOutlook.core.folder.Folder>` to retrieve

        Returns: :class:`Folder <pyOutlook.core.folder.Folder>`

        """
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_id

        r = requests.get(endpoint, headers=self._headers)

        check_response(r)
        return_folder = r.json()
        return Folder._json_to_folder(self, return_folder)

    def _get_messages_from_folder_name(self, folder_name):
        """ Retrieves all messages from a folder, specified by its name. This only works with "Well Known" folders,
        such as 'Inbox' or 'Drafts'.

        Args:
            folder_name (str): The name of the folder to retrieve

        Returns: List[:class:`Message <pyOutlook.core.message.Message>` ]

        """
        r = requests.get('https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_name + '/messages',
                         headers=self._headers)
        check_response(r)
        return Message._json_to_messages(self, r.json())
