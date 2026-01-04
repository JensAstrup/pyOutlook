"""Comprehensive unit tests for src/pyOutlook/core/main.py

Tests cover all classes, methods, and logic branches in the OutlookAccount class.
"""
import json
import unittest
from datetime import datetime
from unittest import mock
from unittest.mock import MagicMock, Mock, patch, call

import requests

from pyOutlook.core.main import OutlookAccount
from pyOutlook.services.message import MessageService
from pyOutlook.services.folder import FolderService
from pyOutlook.services.contact import ContactService


class OutlookAccountTestCase(unittest.TestCase):
    """Test cases for OutlookAccount class initialization and properties"""

    def test_init__creates_account_with_access_token(self):
        """Test that OutlookAccount initializes with access token"""
        token = 'test_access_token_123'
        account = OutlookAccount(token)

        self.assertEqual(account.access_token, token)
        self.assertIsNone(account._auto_reply)
        self.assertIsNone(account._contact_overrides)

    def test_init__creates_service_instances(self):
        """Test that OutlookAccount initializes all service instances"""
        account = OutlookAccount('test_token')

        self.assertIsInstance(account.messages, MessageService)
        self.assertIsInstance(account.folders, FolderService)
        self.assertIsInstance(account.contacts, ContactService)
        self.assertIs(account.messages.account, account)
        self.assertIs(account.folders.account, account)
        self.assertIs(account.contacts.account, account)

    def test_init__requires_access_token(self):
        """Test that OutlookAccount requires an access token parameter"""
        with self.assertRaises(TypeError):
            OutlookAccount()

    def test_headers__returns_authorization_and_content_type(self):
        """Test that _headers property returns correct headers"""
        token = 'my_test_token'
        account = OutlookAccount(token)

        headers = account._headers

        self.assertEqual(headers['Authorization'], f'Bearer {token}')
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(len(headers), 2)

    def test_headers__creates_new_dict_each_time(self):
        """Test that _headers property creates a new dict on each access"""
        account = OutlookAccount('test_token')

        headers1 = account._headers
        headers2 = account._headers

        # Should be equal but not the same object
        self.assertEqual(headers1, headers2)
        self.assertIsNot(headers1, headers2)


class AutoReplyMessageTestCase(unittest.TestCase):
    """Test cases for auto_reply_message property"""

    @patch('pyOutlook.core.main.requests.get')
    @patch('pyOutlook.core.main.check_response')
    def test_auto_reply_message__fetches_from_api_when_none(self, mock_check, mock_get):
        """Test that auto_reply_message fetches from API when _auto_reply is None"""
        account = OutlookAccount('test_token')
        mock_response = Mock()
        mock_response.json.return_value = {
            'automaticReplies': {
                'internalReplyMessage': 'Out of office'
            }
        }
        mock_get.return_value = mock_response

        result = account.auto_reply_message

        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/mailboxSettings/',
            headers=account._headers,
            timeout=10
        )
        mock_check.assert_called_once_with(mock_response)
        self.assertEqual(result, 'Out of office')
        self.assertEqual(account._auto_reply, 'Out of office')

    def test_auto_reply_message__returns_cached_value(self):
        """Test that auto_reply_message returns cached value without API call"""
        account = OutlookAccount('test_token')
        account._auto_reply = 'Cached message'

        with patch('pyOutlook.core.main.requests.get') as mock_get:
            result = account.auto_reply_message

            mock_get.assert_not_called()
            self.assertEqual(result, 'Cached message')

    @patch('pyOutlook.core.main.OutlookAccount.set_auto_reply')
    def test_auto_reply_message__setter_calls_set_auto_reply(self, mock_set_auto_reply):
        """Test that setting auto_reply_message calls set_auto_reply"""
        account = OutlookAccount('test_token')

        account.auto_reply_message = 'New message'

        mock_set_auto_reply.assert_called_once_with('New message')


class SetAutoReplyTestCase(unittest.TestCase):
    """Test cases for set_auto_reply method"""

    @patch('pyOutlook.core.main.requests.patch')
    def test_set_auto_reply__with_message_only(self, mock_patch):
        """Test set_auto_reply with only message parameter"""
        account = OutlookAccount('test_token')
        message = 'I am out of office'

        account.set_auto_reply(message)

        # Verify the request was made
        mock_patch.assert_called_once()
        call_args = mock_patch.call_args

        # Check URL
        self.assertEqual(call_args[0][0], 'https://graph.microsoft.com/v1.0/me/MailboxSettings')

        # Check headers
        self.assertEqual(call_args[1]['headers'], account._headers)

        # Check timeout
        self.assertEqual(call_args[1]['timeout'], 10)

        # Check data
        data = json.loads(call_args[1]['data'])
        self.assertEqual(data['@odata.context'],
                        'https://outlook.office.com/api/v2.0/$metadata#Me/MailboxSettings')
        self.assertEqual(data['AutomaticRepliesSetting']['Status'],
                        OutlookAccount.AutoReplyStatus.ALWAYS_ENABLED)
        self.assertEqual(data['AutomaticRepliesSetting']['ExternalAudience'],
                        OutlookAccount.AutoReplyAudience.ALL)
        self.assertEqual(data['AutomaticRepliesSetting']['InternalReplyMessage'], message)
        self.assertEqual(data['AutomaticRepliesSetting']['ExternalReplyMessage'], message)

        # Check that _auto_reply is updated
        self.assertEqual(account._auto_reply, message)

    @patch('pyOutlook.core.main.requests.patch')
    def test_set_auto_reply__with_external_message(self, mock_patch):
        """Test set_auto_reply with separate external message"""
        account = OutlookAccount('test_token')
        internal_message = 'Internal reply'
        external_message = 'External reply'

        account.set_auto_reply(internal_message, external_message=external_message)

        data = json.loads(mock_patch.call_args[1]['data'])
        self.assertEqual(data['AutomaticRepliesSetting']['InternalReplyMessage'], internal_message)
        self.assertEqual(data['AutomaticRepliesSetting']['ExternalReplyMessage'], external_message)

    @patch('pyOutlook.core.main.requests.patch')
    def test_set_auto_reply__with_custom_status(self, mock_patch):
        """Test set_auto_reply with custom status parameter"""
        account = OutlookAccount('test_token')

        account.set_auto_reply('message', status=OutlookAccount.AutoReplyStatus.DISABLED)

        data = json.loads(mock_patch.call_args[1]['data'])
        self.assertEqual(data['AutomaticRepliesSetting']['Status'],
                        OutlookAccount.AutoReplyStatus.DISABLED)

    @patch('pyOutlook.core.main.requests.patch')
    def test_set_auto_reply__with_custom_audience(self, mock_patch):
        """Test set_auto_reply with custom audience parameter"""
        account = OutlookAccount('test_token')

        account.set_auto_reply('message', audience=OutlookAccount.AutoReplyAudience.CONTACTS_ONLY)

        data = json.loads(mock_patch.call_args[1]['data'])
        self.assertEqual(data['AutomaticRepliesSetting']['ExternalAudience'],
                        OutlookAccount.AutoReplyAudience.CONTACTS_ONLY)

    @patch('pyOutlook.core.main.requests.patch')
    def test_set_auto_reply__with_start_and_end_dates(self, mock_patch):
        """Test set_auto_reply with start and end datetime parameters"""
        account = OutlookAccount('test_token')
        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 10, 18, 0, 0)

        account.set_auto_reply('message', start=start, end=end)

        data = json.loads(mock_patch.call_args[1]['data'])
        self.assertEqual(data['AutomaticRepliesSetting']['ScheduledStartDateTime']['DateTime'],
                        str(start))
        self.assertEqual(data['AutomaticRepliesSetting']['ScheduledEndDateTime']['DateTime'],
                        str(end))

    def test_set_auto_reply__raises_error_when_only_start_provided(self):
        """Test set_auto_reply raises ValueError when only start date is provided"""
        account = OutlookAccount('test_token')
        start = datetime(2024, 1, 1, 10, 0, 0)

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('message', start=start)

    def test_set_auto_reply__raises_error_when_only_end_provided(self):
        """Test set_auto_reply raises ValueError when only end date is provided"""
        account = OutlookAccount('test_token')
        end = datetime(2024, 1, 10, 18, 0, 0)

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('message', end=end)

    def test_set_auto_reply__raises_error_when_start_not_datetime(self):
        """Test set_auto_reply raises ValueError when start is not datetime"""
        account = OutlookAccount('test_token')
        end = datetime(2024, 1, 10, 18, 0, 0)

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('message', start='not a date', end=end)

    def test_set_auto_reply__raises_error_when_end_not_datetime(self):
        """Test set_auto_reply raises ValueError when end is not datetime"""
        account = OutlookAccount('test_token')
        start = datetime(2024, 1, 1, 10, 0, 0)

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('message', start=start, end='not a date')

    def test_set_auto_reply__raises_error_when_start_is_integer(self):
        """Test set_auto_reply raises ValueError when start is integer"""
        account = OutlookAccount('test_token')
        end = datetime(2024, 1, 10, 18, 0, 0)

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('message', start=12345, end=end)

    def test_set_auto_reply__raises_error_when_end_is_integer(self):
        """Test set_auto_reply raises ValueError when end is integer"""
        account = OutlookAccount('test_token')
        start = datetime(2024, 1, 1, 10, 0, 0)

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('message', start=start, end=12345)

    @patch('pyOutlook.core.main.requests.patch')
    def test_set_auto_reply__no_schedule_when_dates_none(self, mock_patch):
        """Test set_auto_reply doesn't include schedule when dates are None"""
        account = OutlookAccount('test_token')

        account.set_auto_reply('message', start=None, end=None)

        data = json.loads(mock_patch.call_args[1]['data'])
        self.assertNotIn('ScheduledStartDateTime', data['AutomaticRepliesSetting'])
        self.assertNotIn('ScheduledEndDateTime', data['AutomaticRepliesSetting'])

    @patch('pyOutlook.core.main.requests.patch')
    def test_set_auto_reply__with_all_parameters(self, mock_patch):
        """Test set_auto_reply with all parameters provided"""
        account = OutlookAccount('test_token')
        internal_message = 'Internal OOO'
        external_message = 'External OOO'
        start = datetime(2024, 6, 1, 9, 0, 0)
        end = datetime(2024, 6, 15, 17, 0, 0)
        status = OutlookAccount.AutoReplyStatus.SCHEDULED
        audience = OutlookAccount.AutoReplyAudience.INTERNAL_ONLY

        account.set_auto_reply(
            internal_message,
            status=status,
            start=start,
            end=end,
            external_message=external_message,
            audience=audience
        )

        mock_patch.assert_called_once()
        data = json.loads(mock_patch.call_args[1]['data'])

        self.assertEqual(data['AutomaticRepliesSetting']['Status'], status)
        self.assertEqual(data['AutomaticRepliesSetting']['ExternalAudience'], audience)
        self.assertEqual(data['AutomaticRepliesSetting']['InternalReplyMessage'], internal_message)
        self.assertEqual(data['AutomaticRepliesSetting']['ExternalReplyMessage'], external_message)
        self.assertEqual(data['AutomaticRepliesSetting']['ScheduledStartDateTime']['DateTime'],
                        str(start))
        self.assertEqual(data['AutomaticRepliesSetting']['ScheduledEndDateTime']['DateTime'],
                        str(end))
        self.assertEqual(account._auto_reply, internal_message)


class InboxTestCase(unittest.TestCase):
    """Test cases for inbox method"""

    @patch.object(MessageService, 'from_folder')
    def test_inbox__calls_messages_from_folder(self, mock_from_folder):
        """Test that inbox calls messages.from_folder with 'Inbox'"""
        account = OutlookAccount('test_token')
        mock_messages = [Mock(), Mock()]
        mock_from_folder.return_value = mock_messages

        result = account.inbox()

        mock_from_folder.assert_called_once_with('Inbox')
        self.assertEqual(result, mock_messages)

    @patch.object(MessageService, 'from_folder')
    def test_inbox__returns_message_list(self, mock_from_folder):
        """Test that inbox returns list of messages"""
        account = OutlookAccount('test_token')
        expected = ['msg1', 'msg2', 'msg3']
        mock_from_folder.return_value = expected

        result = account.inbox()

        self.assertEqual(result, expected)


class SentMessagesTestCase(unittest.TestCase):
    """Test cases for sent_messages method"""

    @patch.object(MessageService, 'from_folder')
    def test_sent_messages__calls_messages_from_folder(self, mock_from_folder):
        """Test that sent_messages calls messages.from_folder with 'SentItems'"""
        account = OutlookAccount('test_token')
        mock_messages = [Mock(), Mock()]
        mock_from_folder.return_value = mock_messages

        result = account.sent_messages()

        mock_from_folder.assert_called_once_with('SentItems')
        self.assertEqual(result, mock_messages)

    @patch.object(MessageService, 'from_folder')
    def test_sent_messages__returns_message_list(self, mock_from_folder):
        """Test that sent_messages returns list of messages"""
        account = OutlookAccount('test_token')
        expected = ['sent1', 'sent2']
        mock_from_folder.return_value = expected

        result = account.sent_messages()

        self.assertEqual(result, expected)


class DeletedMessagesTestCase(unittest.TestCase):
    """Test cases for deleted_messages method"""

    @patch.object(MessageService, 'from_folder')
    def test_deleted_messages__calls_messages_from_folder(self, mock_from_folder):
        """Test that deleted_messages calls messages.from_folder with 'DeletedItems'"""
        account = OutlookAccount('test_token')
        mock_messages = [Mock(), Mock()]
        mock_from_folder.return_value = mock_messages

        result = account.deleted_messages()

        mock_from_folder.assert_called_once_with('DeletedItems')
        self.assertEqual(result, mock_messages)

    @patch.object(MessageService, 'from_folder')
    def test_deleted_messages__returns_message_list(self, mock_from_folder):
        """Test that deleted_messages returns list of messages"""
        account = OutlookAccount('test_token')
        expected = ['deleted1', 'deleted2', 'deleted3']
        mock_from_folder.return_value = expected

        result = account.deleted_messages()

        self.assertEqual(result, expected)


class DraftMessagesTestCase(unittest.TestCase):
    """Test cases for draft_messages method"""

    @patch.object(MessageService, 'from_folder')
    def test_draft_messages__calls_messages_from_folder(self, mock_from_folder):
        """Test that draft_messages calls messages.from_folder with 'Drafts'"""
        account = OutlookAccount('test_token')
        mock_messages = [Mock()]
        mock_from_folder.return_value = mock_messages

        result = account.draft_messages()

        mock_from_folder.assert_called_once_with('Drafts')
        self.assertEqual(result, mock_messages)

    @patch.object(MessageService, 'from_folder')
    def test_draft_messages__returns_message_list(self, mock_from_folder):
        """Test that draft_messages returns list of messages"""
        account = OutlookAccount('test_token')
        expected = ['draft1']
        mock_from_folder.return_value = expected

        result = account.draft_messages()

        self.assertEqual(result, expected)


class AutoReplyStatusTestCase(unittest.TestCase):
    """Test cases for AutoReplyStatus inner class"""

    def test_auto_reply_status__has_disabled_constant(self):
        """Test AutoReplyStatus.DISABLED constant"""
        self.assertEqual(OutlookAccount.AutoReplyStatus.DISABLED, 'Disabled')

    def test_auto_reply_status__has_always_enabled_constant(self):
        """Test AutoReplyStatus.ALWAYS_ENABLED constant"""
        self.assertEqual(OutlookAccount.AutoReplyStatus.ALWAYS_ENABLED, 'AlwaysEnabled')

    def test_auto_reply_status__has_scheduled_constant(self):
        """Test AutoReplyStatus.SCHEDULED constant"""
        self.assertEqual(OutlookAccount.AutoReplyStatus.SCHEDULED, 'Scheduled')


class AutoReplyAudienceTestCase(unittest.TestCase):
    """Test cases for AutoReplyAudience inner class"""

    def test_auto_reply_audience__has_internal_only_constant(self):
        """Test AutoReplyAudience.INTERNAL_ONLY constant"""
        self.assertEqual(OutlookAccount.AutoReplyAudience.INTERNAL_ONLY, 'None')

    def test_auto_reply_audience__has_contacts_only_constant(self):
        """Test AutoReplyAudience.CONTACTS_ONLY constant"""
        self.assertEqual(OutlookAccount.AutoReplyAudience.CONTACTS_ONLY, 'ContactsOnly')

    def test_auto_reply_audience__has_all_constant(self):
        """Test AutoReplyAudience.ALL constant"""
        self.assertEqual(OutlookAccount.AutoReplyAudience.ALL, 'All')


if __name__ == '__main__':
    unittest.main()
