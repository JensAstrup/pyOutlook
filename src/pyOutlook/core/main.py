# Authorization and misc functions
import json
import logging

from datetime import datetime

import requests

from pyOutlook.internal.utils import check_response
from pyOutlook.services.message import MessageService
from pyOutlook.services.folder import FolderService
from pyOutlook.services.contact import ContactService

log = logging.getLogger('pyOutlook')
__all__ = ['OutlookAccount']


class OutlookAccount(object):
    """Sets up access to an Outlook account via the Microsoft Graph API.

    This is the main entry point for interacting with an Outlook account.
    It provides access to messages, folders, and contacts through service objects.

    :param access_token: OAuth token from Microsoft allowing access to a user's account.
    :type access_token: str

    :ivar access_token: The OAuth access token for API authentication.
    :ivar messages: Service for retrieving and sending messages.
    :vartype messages: MessageService
    :ivar folders: Service for retrieving and managing mail folders.
    :vartype folders: FolderService
    :ivar contacts: Service for managing contacts and focused inbox overrides.
    :vartype contacts: ContactService

    Example::

        # Initialize with an OAuth token
        account = OutlookAccount('your-access-token')

        # Access inbox messages
        inbox_messages = account.inbox()

        # Get all folders
        all_folders = account.folders.all()

        # Send a message
        account.messages.send(
            subject='Hello',
            body='<p>Hello World!</p>',
            to=['recipient@example.com']
        )
    """

    def __init__(self, access_token: str):
        self.access_token = access_token
        self._auto_reply = None
        self._contact_overrides = None
        self.messages = MessageService(self)  # pyrefly: ignore
        self.folders = FolderService(self)  # pyrefly: ignore
        self.contacts = ContactService(self)  # pyrefly: ignore

    @property
    def _headers(self):
        return {'Authorization': f'Bearer {self.access_token}', 'Content-Type': 'application/json'}

    @property
    def auto_reply_message(self) -> str:
        """The account's internal auto reply message.

        Setting this property will change the auto reply message of the account,
        automatically enabling auto-replies (but not altering the schedule).

        :returns: The current internal auto reply message.
        :rtype: str

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.
        """
        if self._auto_reply is None:
            r = requests.get('https://graph.microsoft.com/v1.0/me/mailboxSettings/',
                             headers=self._headers, timeout=10)
            check_response(r)
            data = r.json()
            self._auto_reply = data.get('automaticReplies').get('internalReplyMessage')

        return self._auto_reply

    @auto_reply_message.setter
    def auto_reply_message(self, value: str):
        """Set the auto reply message.

        :param value: The new auto reply message.
        :type value: str
        """
        self.set_auto_reply(value)

    class AutoReplyAudience(object):
        """Constants for specifying who receives automatic replies.

        :cvar INTERNAL_ONLY: Send auto-replies only to internal organization members.
        :cvar CONTACTS_ONLY: Send auto-replies only to contacts.
        :cvar ALL: Send auto-replies to all senders.
        """
        INTERNAL_ONLY = 'None'
        CONTACTS_ONLY = 'ContactsOnly'
        ALL = 'All'

    class AutoReplyStatus(object):
        """Constants for automatic reply status.

        :cvar DISABLED: Auto-replies are disabled.
        :cvar ALWAYS_ENABLED: Auto-replies are always sent.
        :cvar SCHEDULED: Auto-replies are sent during a scheduled time window.
        """
        DISABLED = 'Disabled'
        ALWAYS_ENABLED = 'AlwaysEnabled'
        SCHEDULED = 'Scheduled'

    def set_auto_reply(self, message: str, status: str = AutoReplyStatus.ALWAYS_ENABLED,
                       start: datetime | None = None, end: datetime | None = None,
                       external_message: str | None = None,
                       audience: str = AutoReplyAudience.ALL) -> None:
        """Set an automatic reply for the account.

        :param message: The message to be sent in replies. If ``external_message`` is
            provided, this is the message sent to internal recipients only.
        :type message: str
        :param status: Whether the auto-reply should be always enabled, scheduled, or
            disabled. Defaults to ``AutoReplyStatus.ALWAYS_ENABLED``.
        :type status: AutoReplyStatus
        :param start: If status is ``SCHEDULED``, when the replies will start being sent.
        :type start: datetime or None
        :param end: If status is ``SCHEDULED``, when the replies will stop being sent.
        :type end: datetime or None
        :param external_message: If provided, this message will be sent to external
            recipients. If not provided, the ``message`` is used for both.
        :type external_message: str or None
        :param audience: Who should receive auto-replies. Defaults to ``AutoReplyAudience.ALL``.
        :type audience: AutoReplyAudience

        :raises ValueError: If only one of ``start`` or ``end`` is provided, or if they
            are not datetime objects.

        Example::

            from datetime import datetime

            # Enable auto-reply for everyone
            account.set_auto_reply('I am currently out of office.')

            # Schedule auto-reply with different internal/external messages
            account.set_auto_reply(
                message='Internal: I am on vacation.',
                external_message='Thank you for your email. I am currently unavailable.',
                status=account.AutoReplyStatus.SCHEDULED,
                start=datetime(2024, 12, 20),
                end=datetime(2024, 12, 31),
                audience=account.AutoReplyAudience.ALL
            )

        .. seealso::
            :class:`AutoReplyStatus` for status options.
            :class:`AutoReplyAudience` for audience options.
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
            '@odata.context': 'https://graph.microsoft.com/v1.0/$metadata#Me/MailboxSettings',
            'AutomaticRepliesSetting': request_data
        }

        requests.patch('https://graph.microsoft.com/v1.0/me/MailboxSettings',
                       headers=self._headers, data=json.dumps(data), timeout=10)

        self._auto_reply = message

    def inbox(self) -> list:
        """Retrieve messages from the account's inbox.

        Returns the default page of messages from the Inbox folder
        (10 items per Microsoft Graph API defaults).

        :returns: Messages from the inbox folder.
        :rtype: list[Message]

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.

        .. seealso:: :meth:`MessageService.from_folder` for more control over retrieval.
        """
        return self.messages.from_folder('Inbox')

    def sent_messages(self) -> list:
        """Retrieve sent messages.

        Returns the default page of messages from the Sent Items folder
        (10 items per Microsoft Graph API defaults).

        :returns: Messages from the sent items folder.
        :rtype: list[Message]

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.
        """
        return self.messages.from_folder('SentItems')

    def deleted_messages(self) -> list:
        """Retrieve deleted messages.

        Returns the default page of messages from the Deleted Items folder
        (10 items per Microsoft Graph API defaults).

        :returns: Messages from the deleted items folder.
        :rtype: list[Message]

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.
        """
        return self.messages.from_folder('DeletedItems')

    def draft_messages(self) -> list:
        """Retrieve draft messages.

        Returns the default page of messages from the Drafts folder
        (10 items per Microsoft Graph API defaults).

        :returns: Messages from the drafts folder.
        :rtype: list[Message]

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.
        """
        return self.messages.from_folder('Drafts')
