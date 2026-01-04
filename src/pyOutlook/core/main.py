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
    '''Sets up access to an Outlook account.

    Attributes:
        access_token: A string OAuth token from Outlook allowing access to a user's account

    '''

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
        ''' The account's Internal auto reply message. Setting the value will change the auto reply message of the
         account, automatically setting the status to enabled (but not altering the schedule). '''
        if self._auto_reply is None:
            r = requests.get('https://graph.microsoft.com/v1.0/me/mailboxSettings/',
                             headers=self._headers, timeout=10)
            check_response(r)
            data = r.json()
            self._auto_reply = data.get('automaticReplies').get('internalReplyMessage')

        return self._auto_reply

    @auto_reply_message.setter
    def auto_reply_message(self, value):
        self.set_auto_reply(value)

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
        ''' Set an automatic reply for the account.
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

        '''

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
            '@odata.context': 'https://outlook.office.com/api/v2.0/$metadata#Me/MailboxSettings',
            'AutomaticRepliesSetting': request_data
        }

        requests.patch('https://graph.microsoft.com/v1.0/me/MailboxSettings',
                       headers=self._headers, data=json.dumps(data), timeout=10)

        self._auto_reply = message

    def inbox(self):
        ''' first ten messages in account's inbox.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>`]

        '''
        return self.messages.from_folder('Inbox')

    def sent_messages(self):
        ''' last ten sent messages.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>`]

        '''
        return self.messages.from_folder('SentItems')

    def deleted_messages(self):
        ''' last ten deleted messages.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>` ]

        '''
        return self.messages.from_folder('DeletedItems')

    def draft_messages(self):
        ''' last ten draft messages.

        Returns:
            List[:class:`Message <pyOutlook.core.message.Message>`]

        '''
        return self.messages.from_folder('Drafts')
