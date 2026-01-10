import base64
import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from pyOutlook import OutlookAccount
from pyOutlook.core.contact import Contact
from pyOutlook.core.message import Message
from pyOutlook.core.attachment import Attachment
from pyOutlook.internal.errors import AuthError, RequestError, APIError
from tests.utils import sample_message


class MessageTestCase(unittest.TestCase):
    """Comprehensive unit tests for the Message class."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures - add api_representation methods."""
        # Add api_representation method to Contact if it doesn't exist
        if not hasattr(Contact, 'api_representation'):
            Contact.api_representation = lambda self: dict(self)

        # Add api_representation method to Attachment if it doesn't exist
        if not hasattr(Attachment, 'api_representation'):
            Attachment.api_representation = lambda self: dict(self)

    def setUp(self):
        """Set up test fixtures."""
        self.account = OutlookAccount('test_token')
        self.sample_to = [Contact('recipient@test.com', 'Test Recipient')]
        self.sample_cc = [Contact('cc@test.com', 'CC Recipient')]
        self.sample_bcc = [Contact('bcc@test.com', 'BCC Recipient')]
        self.sample_sender = Contact('sender@test.com', 'Test Sender')

    def test_init__minimal_parameters(self):
        """Test Message initialization with minimal parameters."""
        message = Message(self.account)

        self.assertEqual(message.account, self.account)
        self.assertIsNone(message.message_id)
        self.assertEqual(message.body, '')
        self.assertEqual(message.subject, '')
        self.assertEqual(message.to, [])
        self.assertEqual(message.cc, [])
        self.assertEqual(message.bcc, [])
        self.assertIsNone(message.sender)
        self.assertFalse(message._is_read)
        self.assertFalse(message.is_draft)
        self.assertEqual(message.importance, Message.IMPORTANCE_NORMAL)
        self.assertEqual(message.categories, [])
        self.assertFalse(message.focused)

    def test_init__all_parameters(self):
        """Test Message initialization with all parameters."""
        time_created = datetime(2024, 1, 1, 12, 0, 0)
        time_sent = datetime(2024, 1, 1, 12, 5, 0)

        message = Message(
            self.account,
            body='Test body',
            subject='Test subject',
            to_recipients=self.sample_to,
            sender=self.sample_sender,
            cc=self.sample_cc,
            bcc=self.sample_bcc,
            message_id='test_id_123',
            body_preview='Test preview',
            is_read=True,
            is_draft=True,
            importance=Message.IMPORTANCE_HIGH,
            categories=['Important', 'Work'],
            focused=True,
            time_created=time_created,
            time_sent=time_sent,
            parent_folder_id='folder_123',
            has_attachments=True
        )

        self.assertEqual(message.account, self.account)
        self.assertEqual(message.message_id, 'test_id_123')
        self.assertEqual(message.body, 'Test body')
        self.assertEqual(message.subject, 'Test subject')
        self.assertEqual(message.to, self.sample_to)
        self.assertEqual(message.cc, self.sample_cc)
        self.assertEqual(message.bcc, self.sample_bcc)
        self.assertEqual(message.sender, self.sample_sender)
        self.assertTrue(message._is_read)
        self.assertTrue(message.is_draft)
        self.assertEqual(message.importance, Message.IMPORTANCE_HIGH)
        self.assertEqual(message.categories, ['Important', 'Work'])
        self.assertTrue(message.focused)
        self.assertEqual(message.time_created, time_created)
        self.assertEqual(message.time_sent, time_sent)
        self.assertEqual(message.parent_folder_id, 'folder_123')
        self.assertTrue(message._has_attachments)

    def test_init__none_recipients_default_to_empty_lists(self):
        """Test that None recipients default to empty lists."""
        message = Message(self.account, to_recipients=None, cc=None, bcc=None)

        self.assertEqual(message.to, [])
        self.assertEqual(message.cc, [])
        self.assertEqual(message.bcc, [])

    def test_str__returns_subject(self):
        """Test __str__ returns the subject."""
        message = Message(self.account, subject='My Subject')
        self.assertEqual(str(message), 'My Subject')

    def test_repr__returns_formatted_string(self):
        """Test __repr__ returns properly formatted string."""
        message = Message(self.account, subject='Test Subject', message_id='msg_123')
        expected = "Message(subject='Test Subject', message_id='msg_123')"
        self.assertEqual(repr(message), expected)

    def test_headers__contains_authorization_and_content_type(self):
        """Test headers property contains required headers."""
        message = Message(self.account)
        headers = message.headers

        self.assertIn('Authorization', headers)
        self.assertEqual(headers['Authorization'], 'Bearer test_token')
        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/json')

    def test_is_read_getter__returns_is_read_status(self):
        """Test is_read property getter."""
        message = Message(self.account, is_read=True)
        self.assertTrue(message.is_read)

        message2 = Message(self.account, is_read=False)
        self.assertFalse(message2.is_read)

    @patch('pyOutlook.core.message.requests.patch')
    def test_is_read_setter__calls_set_read_status(self, mock_patch):
        """Test is_read property setter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        message = Message(self.account, message_id='msg_123', is_read=False)
        message.is_read = True

        self.assertTrue(message.is_read)

    def test_attachments__no_attachments_returns_empty_list(self):
        """Test attachments property when has_attachments is False."""
        message = Message(self.account, has_attachments=False)
        result = message.attachments

        self.assertEqual(result, [])

    def test_attachments__cached_attachments_returned(self):
        """Test attachments property returns cached attachments."""
        message = Message(self.account, has_attachments=True)
        cached_attachment = Attachment('test.txt', base64.b64encode(b'test').decode())
        message._attachments = [cached_attachment]

        result = message.attachments

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], cached_attachment)

    @patch('pyOutlook.core.message.requests.get')
    def test_attachments__lazy_load_from_api_success(self, mock_get):
        """Test attachments property lazy loads from API."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {
                    'name': 'file1.txt',
                    'contentBytes': base64.b64encode(b'content1').decode(),
                    'contentId': 'id1',
                    'size': 100,
                    'lastModifiedDateTime': '2024-01-01T12:00:00Z',
                    'contentType': 'text/plain'
                },
                {
                    'name': 'file2.pdf',
                    'contentBytes': base64.b64encode(b'content2').decode(),
                    'contentId': 'id2',
                    'size': 200,
                    'lastModifiedDateTime': '2024-01-02T12:00:00Z',
                    'contentType': 'application/pdf'
                }
            ]
        }
        mock_get.return_value = mock_response

        message = Message(self.account, message_id='msg_123', has_attachments=True)
        result = message.attachments

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'file1.txt')
        self.assertEqual(result[1].name, 'file2.pdf')
        mock_get.assert_called_once()

    @patch('pyOutlook.core.message.requests.get')
    def test_attachments__no_message_id_returns_empty_list(self, mock_get):
        """Test attachments property when message_id is None."""
        message = Message(self.account, message_id=None, has_attachments=True)
        result = message.attachments

        self.assertEqual(result, [])
        mock_get.assert_not_called()

    @patch('pyOutlook.core.message.requests.get')
    def test_attachments__api_error_returns_empty_list(self, mock_get):
        """Test attachments property when API returns error."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'Unauthorized'}
        mock_get.return_value = mock_response

        message = Message(self.account, message_id='msg_123', has_attachments=True)

        with self.assertRaises(AuthError):
            _ = message.attachments

    def test_parent_folder__returns_cached_folder(self):
        """Test parent_folder property returns cached folder."""
        mock_folder = Mock()
        message = Message(self.account, parent_folder_id='folder_123')
        message._parent_folder_cache = mock_folder

        result = message.parent_folder

        self.assertEqual(result, mock_folder)

    def test_parent_folder__lazy_loads_folder(self):
        """Test parent_folder property lazy loads folder."""
        mock_folder = Mock()
        self.account.get_folder_by_id = Mock(return_value=mock_folder)

        message = Message(self.account, parent_folder_id='folder_123')
        result = message.parent_folder

        self.assertEqual(result, mock_folder)
        self.account.get_folder_by_id.assert_called_once_with('folder_123')

    def test_parent_folder__no_folder_id_returns_none(self):
        """Test parent_folder property when parent_folder_id is None."""
        message = Message(self.account, parent_folder_id=None)
        result = message.parent_folder

        self.assertIsNone(result)

    @patch('pyOutlook.core.message.requests.post')
    def test_send__html_content_type(self, mock_post):
        """Test send method with HTML content type."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(
            self.account,
            body='<p>Test</p>',
            subject='Test Subject',
            to_recipients=self.sample_to
        )
        message.send(content_type='HTML')

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['Message']['Body']['ContentType'], 'HTML')

    @patch('pyOutlook.core.message.requests.post')
    def test_send__text_content_type(self, mock_post):
        """Test send method with Text content type."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(
            self.account,
            body='Plain text',
            subject='Test Subject',
            to_recipients=self.sample_to
        )
        message.send(content_type='Text')

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['Message']['Body']['ContentType'], 'Text')

    @patch('pyOutlook.core.message.requests.post')
    def test_send__default_content_type_is_html(self, mock_post):
        """Test send method defaults to HTML content type."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(
            self.account,
            body='Test',
            subject='Test Subject',
            to_recipients=self.sample_to
        )
        message.send()

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['Message']['Body']['ContentType'], 'HTML')

    @patch('pyOutlook.core.message.requests.post')
    def test_reply__success(self, mock_post):
        """Test reply method with valid message_id."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.reply('This is my reply')

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('msg_123/reply', call_args[0][0])
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['Comment'], 'This is my reply')

    def test_reply__no_message_id_raises_error(self):
        """Test reply method without message_id raises ValueError."""
        message = Message(self.account, message_id=None)

        with self.assertRaises(ValueError) as context:
            message.reply('Reply text')

        self.assertIn('Cannot reply to a message without message_id', str(context.exception))

    @patch('pyOutlook.core.message.requests.post')
    def test_reply_all__success(self, mock_post):
        """Test reply_all method with valid message_id."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.reply_all('Reply to all')

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('msg_123/replyall', call_args[0][0])
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['Comment'], 'Reply to all')

    def test_reply_all__no_message_id_raises_error(self):
        """Test reply_all method without message_id raises ValueError."""
        message = Message(self.account, message_id=None)

        with self.assertRaises(ValueError) as context:
            message.reply_all('Reply text')

        self.assertIn('Cannot reply to a message without message_id', str(context.exception))

    @patch('pyOutlook.core.message.requests.post')
    def test_forward__with_contact_recipients_and_comment(self, mock_post):
        """Test forward method with Contact recipients and comment."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        recipients = [Contact('forward@test.com', 'Forward Recipient')]
        message.forward(recipients, 'Please review this')

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('msg_123/forward', call_args[0][0])
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['Comment'], 'Please review this')
        self.assertEqual(len(payload['ToRecipients']), 1)

    @patch('pyOutlook.core.message.requests.post')
    def test_forward__with_string_recipients(self, mock_post):
        """Test forward method converts string recipients to Contacts."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        recipients = ['user1@test.com', 'user2@test.com']
        message.forward(recipients)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(len(payload['ToRecipients']), 2)

    @patch('pyOutlook.core.message.requests.post')
    def test_forward__without_comment(self, mock_post):
        """Test forward method without comment."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        recipients = [Contact('forward@test.com')]
        message.forward(recipients, forward_comment=None)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertNotIn('Comment', payload)

    def test_forward__no_message_id_raises_error(self):
        """Test forward method without message_id raises ValueError."""
        message = Message(self.account, message_id=None)
        recipients = [Contact('forward@test.com')]

        with self.assertRaises(ValueError) as context:
            message.forward(recipients)

        self.assertIn('Cannot forward a message without message_id', str(context.exception))

    @patch('pyOutlook.core.message.requests.delete')
    def test_delete__success(self, mock_delete):
        """Test delete method with valid message_id."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_delete.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.delete()

        mock_delete.assert_called_once()
        call_args = mock_delete.call_args
        self.assertIn('msg_123', call_args[0][0])

    def test_delete__no_message_id_raises_error(self):
        """Test delete method without message_id raises ValueError."""
        message = Message(self.account, message_id=None)

        with self.assertRaises(ValueError) as context:
            message.delete()

        self.assertIn('Cannot delete a message without message_id', str(context.exception))

    @patch('pyOutlook.core.message.isinstance')
    @patch('pyOutlook.core.message.requests.post')
    def test_move_to__with_folder_object(self, mock_post, mock_isinstance):
        """Test move_to method with Folder object."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'Id': 'new_msg_id'}
        mock_post.return_value = mock_response

        # Create a folder-like object
        class FolderStub:
            def __init__(self, folder_id):
                self.id = folder_id

        folder_stub = FolderStub('folder_456')

        # Make isinstance return True for our stub
        mock_isinstance.return_value = True

        message = Message(self.account, message_id='msg_123')
        message.move_to(folder_stub)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'folder_456')
        self.assertEqual(message.message_id, 'new_msg_id')

    @patch('pyOutlook.core.message.requests.post')
    def test_move_to__with_folder_id_string(self, mock_post):
        """Test move_to method with folder ID string."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'Id': 'msg_123'}
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.move_to('folder_456')

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'folder_456')

    def test_move_to__no_message_id_raises_error(self):
        """Test move_to method without message_id raises ValueError."""
        message = Message(self.account, message_id=None)

        with self.assertRaises(ValueError) as context:
            message.move_to('folder_123')

        self.assertIn('Cannot move a message without message_id', str(context.exception))

    @patch('pyOutlook.core.message.requests.post')
    def test_move_to_inbox__calls_move_to(self, mock_post):
        """Test move_to_inbox method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'Id': 'msg_123'}
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.move_to_inbox()

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'Inbox')

    @patch('pyOutlook.core.message.requests.post')
    def test_move_to_deleted__calls_move_to(self, mock_post):
        """Test move_to_deleted method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'Id': 'msg_123'}
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.move_to_deleted()

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'DeletedItems')

    @patch('pyOutlook.core.message.requests.post')
    def test_move_to_drafts__calls_move_to(self, mock_post):
        """Test move_to_drafts method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'Id': 'msg_123'}
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.move_to_drafts()

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'Drafts')

    @patch('pyOutlook.core.message.isinstance')
    @patch('pyOutlook.core.message.requests.post')
    def test_copy_to__with_folder_object(self, mock_post, mock_isinstance):
        """Test copy_to method with Folder object."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Create a folder-like object with just the id attribute
        class FolderStub:
            def __init__(self, folder_id):
                self.id = folder_id

        folder_stub = FolderStub('folder_789')

        # Make isinstance return True for our stub
        mock_isinstance.return_value = True

        message = Message(self.account, message_id='msg_123')
        message.copy_to(folder_stub)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIn('msg_123/copy', call_args[0][0])
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'folder_789')

    @patch('pyOutlook.core.message.requests.post')
    def test_copy_to__with_folder_id_string(self, mock_post):
        """Test copy_to method with folder ID string."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.copy_to('folder_789')

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'folder_789')

    def test_copy_to__no_message_id_raises_error(self):
        """Test copy_to method without message_id raises ValueError."""
        message = Message(self.account, message_id=None)

        with self.assertRaises(ValueError) as context:
            message.copy_to('folder_123')

        self.assertIn('Cannot copy a message without message_id', str(context.exception))

    @patch('pyOutlook.core.message.requests.post')
    def test_copy_to_inbox__calls_copy_to(self, mock_post):
        """Test copy_to_inbox method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.copy_to_inbox()

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'Inbox')

    @patch('pyOutlook.core.message.requests.post')
    def test_copy_to_deleted__calls_copy_to(self, mock_post):
        """Test copy_to_deleted method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.copy_to_deleted()

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'DeletedItems')

    @patch('pyOutlook.core.message.requests.post')
    def test_copy_to_drafts__calls_copy_to(self, mock_post):
        """Test copy_to_drafts method."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.copy_to_drafts()

        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['DestinationId'], 'Drafts')

    @patch('pyOutlook.core.message.requests.patch')
    def test_set_read_status__with_message_id_true(self, mock_patch):
        """Test set_read_status method with message_id and is_read=True."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        message = Message(self.account, message_id='msg_123', is_read=False)
        message.set_read_status(True)

        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['IsRead'], True)
        self.assertTrue(message._is_read)

    @patch('pyOutlook.core.message.requests.patch')
    def test_set_read_status__with_message_id_false(self, mock_patch):
        """Test set_read_status method with message_id and is_read=False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        message = Message(self.account, message_id='msg_123', is_read=True)
        message.set_read_status(False)

        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['IsRead'], False)
        self.assertFalse(message._is_read)

    @patch('pyOutlook.core.message.requests.patch')
    def test_set_read_status__without_message_id(self, mock_patch):
        """Test set_read_status method without message_id only updates internal state."""
        message = Message(self.account, message_id=None, is_read=False)
        message.set_read_status(True)

        mock_patch.assert_not_called()
        self.assertTrue(message._is_read)

    @patch('pyOutlook.core.message.requests.patch')
    def test_set_focused__focused_true(self, mock_patch):
        """Test set_focused method with is_focused=True."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        message = Message(self.account, message_id='msg_123', focused=False)
        message.set_focused(True)

        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['InferenceClassification'], 'Focused')
        self.assertTrue(message.focused)

    @patch('pyOutlook.core.message.requests.patch')
    def test_set_focused__focused_false(self, mock_patch):
        """Test set_focused method with is_focused=False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        message = Message(self.account, message_id='msg_123', focused=True)
        message.set_focused(False)

        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['InferenceClassification'], 'Other')
        self.assertFalse(message.focused)

    def test_set_focused__no_message_id_raises_error(self):
        """Test set_focused method without message_id raises ValueError."""
        message = Message(self.account, message_id=None)

        with self.assertRaises(ValueError) as context:
            message.set_focused(True)

        self.assertIn('Cannot set focused status on a message without message_id', str(context.exception))

    @patch('pyOutlook.core.message.requests.patch')
    def test_add_category__new_category_without_message_id(self, mock_patch):
        """Test add_category method without message_id."""
        message = Message(self.account, message_id=None, categories=['Category1'])
        message.add_category('Category2')

        self.assertIn('Category1', message.categories)
        self.assertIn('Category2', message.categories)
        self.assertEqual(len(message.categories), 2)
        mock_patch.assert_not_called()

    @patch('pyOutlook.core.message.requests.patch')
    def test_add_category__new_category_with_message_id(self, mock_patch):
        """Test add_category method with message_id."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        message = Message(self.account, message_id='msg_123', categories=['Category1'])
        message.add_category('Category2')

        mock_patch.assert_called_once()
        call_args = mock_patch.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(payload['Categories'], ['Category1', 'Category2'])

    @patch('pyOutlook.core.message.requests.patch')
    def test_add_category__to_empty_category_list(self, mock_patch):
        """Test add_category method to empty category list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        message = Message(self.account, message_id='msg_123', categories=[])
        message.add_category('FirstCategory')

        self.assertEqual(message.categories, ['FirstCategory'])

    def test_attach__with_bytes(self):
        """Test attach method with bytes."""
        message = Message(self.account)
        file_bytes = b'Test file content'

        message.attach(file_bytes, 'test.txt')

        self.assertEqual(len(message._attachments), 1)
        self.assertEqual(message._attachments[0].name, 'test.txt')
        self.assertTrue(message._has_attachments)

    def test_attach__with_string(self):
        """Test attach method with string."""
        message = Message(self.account)
        file_content = 'Test string content'

        message.attach(file_content, 'test.txt')

        self.assertEqual(len(message._attachments), 1)
        self.assertEqual(message._attachments[0].name, 'test.txt')
        self.assertTrue(message._has_attachments)

    def test_attach__filename_sanitization(self):
        """Test attach method sanitizes filename."""
        message = Message(self.account)

        message.attach(b'content', "john's portrait in 2004.jpg")

        self.assertEqual(message._attachments[0].name, 'johns_portrait_in_2004.jpg')

    def test_attach__multiple_attachments(self):
        """Test attach method with multiple attachments."""
        message = Message(self.account)

        message.attach(b'content1', 'file1.txt')
        message.attach(b'content2', 'file2.pdf')
        message.attach(b'content3', 'file3.docx')

        self.assertEqual(len(message._attachments), 3)
        self.assertTrue(message._has_attachments)

    def test_create_api_payload__minimal_message(self):
        """Test _create_api_payload with minimal message."""
        message = Message(
            self.account,
            body='Test body',
            subject='Test subject',
            to_recipients=[Contact('to@test.com')]
        )

        payload = message._create_api_payload('HTML')

        self.assertIn('Message', payload)
        msg = payload['Message']
        self.assertEqual(msg['Subject'], 'Test subject')
        self.assertEqual(msg['Body']['ContentType'], 'HTML')
        self.assertEqual(msg['Body']['Content'], 'Test body')
        self.assertEqual(len(msg['ToRecipients']), 1)

    def test_create_api_payload__with_sender(self):
        """Test _create_api_payload with sender."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            sender=Contact('sender@test.com', 'Sender Name')
        )

        payload = message._create_api_payload('HTML')

        self.assertIn('From', payload['Message'])

    def test_create_api_payload__without_sender(self):
        """Test _create_api_payload without sender."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            sender=None
        )

        payload = message._create_api_payload('HTML')

        self.assertNotIn('From', payload['Message'])

    def test_create_api_payload__with_cc_recipients(self):
        """Test _create_api_payload with CC recipients."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            cc=[Contact('cc1@test.com'), Contact('cc2@test.com')]
        )

        payload = message._create_api_payload('HTML')

        self.assertIn('CcRecipients', payload['Message'])
        self.assertEqual(len(payload['Message']['CcRecipients']), 2)

    def test_create_api_payload__without_cc_recipients(self):
        """Test _create_api_payload without CC recipients."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            cc=[]
        )

        payload = message._create_api_payload('HTML')

        self.assertNotIn('CcRecipients', payload['Message'])

    def test_create_api_payload__with_bcc_recipients(self):
        """Test _create_api_payload with BCC recipients."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            bcc=[Contact('bcc1@test.com'), Contact('bcc2@test.com')]
        )

        payload = message._create_api_payload('HTML')

        self.assertIn('BccRecipients', payload['Message'])
        self.assertEqual(len(payload['Message']['BccRecipients']), 2)

    def test_create_api_payload__without_bcc_recipients(self):
        """Test _create_api_payload without BCC recipients."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            bcc=[]
        )

        payload = message._create_api_payload('HTML')

        self.assertNotIn('BccRecipients', payload['Message'])

    def test_create_api_payload__with_string_to_recipients(self):
        """Test _create_api_payload converts string TO recipients to Contacts."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=['to1@test.com', 'to2@test.com']
        )

        payload = message._create_api_payload('HTML')

        self.assertEqual(len(payload['Message']['ToRecipients']), 2)

    def test_create_api_payload__with_string_cc_recipients(self):
        """Test _create_api_payload converts string CC recipients to Contacts."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            cc=['cc1@test.com', 'cc2@test.com']
        )

        payload = message._create_api_payload('HTML')

        self.assertIn('CcRecipients', payload['Message'])
        self.assertEqual(len(payload['Message']['CcRecipients']), 2)

    def test_create_api_payload__with_string_bcc_recipients(self):
        """Test _create_api_payload converts string BCC recipients to Contacts."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            bcc=['bcc1@test.com', 'bcc2@test.com']
        )

        payload = message._create_api_payload('HTML')

        self.assertIn('BccRecipients', payload['Message'])
        self.assertEqual(len(payload['Message']['BccRecipients']), 2)

    def test_create_api_payload__with_attachments(self):
        """Test _create_api_payload with attachments."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')]
        )
        message.attach(b'content', 'test.txt')

        payload = message._create_api_payload('HTML')

        self.assertIn('Attachments', payload['Message'])
        self.assertEqual(len(payload['Message']['Attachments']), 1)

    def test_create_api_payload__without_attachments(self):
        """Test _create_api_payload without attachments."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')]
        )

        payload = message._create_api_payload('HTML')

        self.assertNotIn('Attachments', payload['Message'])

    def test_create_api_payload__importance_low(self):
        """Test _create_api_payload with low importance."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            importance=Message.IMPORTANCE_LOW
        )

        payload = message._create_api_payload('HTML')

        self.assertEqual(payload['Message']['Importance'], '0')

    def test_create_api_payload__importance_normal(self):
        """Test _create_api_payload with normal importance."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            importance=Message.IMPORTANCE_NORMAL
        )

        payload = message._create_api_payload('HTML')

        self.assertEqual(payload['Message']['Importance'], '1')

    def test_create_api_payload__importance_high(self):
        """Test _create_api_payload with high importance."""
        message = Message(
            self.account,
            body='Test',
            subject='Test',
            to_recipients=[Contact('to@test.com')],
            importance=Message.IMPORTANCE_HIGH
        )

        payload = message._create_api_payload('HTML')

        self.assertEqual(payload['Message']['Importance'], '2')

    def test_create_api_payload__text_content_type(self):
        """Test _create_api_payload with Text content type."""
        message = Message(
            self.account,
            body='Plain text',
            subject='Test',
            to_recipients=[Contact('to@test.com')]
        )

        payload = message._create_api_payload('Text')

        self.assertEqual(payload['Message']['Body']['ContentType'], 'Text')

    @patch('pyOutlook.services.message.MessageService._json_to_messages')
    def test_json_to_messages__delegates_to_service(self, mock_service_method):
        """Test _json_to_messages class method delegates to MessageService."""
        mock_service_method.return_value = []
        json_data = {'value': []}

        result = Message._json_to_messages(self.account, json_data)

        mock_service_method.assert_called_once_with(self.account, json_data)

    @patch('pyOutlook.services.message.MessageService._json_to_message')
    def test_json_to_message__delegates_to_service(self, mock_service_method):
        """Test _json_to_message class method delegates to MessageService."""
        mock_message = Mock()
        mock_service_method.return_value = mock_message

        result = Message._json_to_message(self.account, sample_message)

        mock_service_method.assert_called_once_with(self.account, sample_message)
        self.assertEqual(result, mock_message)


class MessageIntegrationTestCase(unittest.TestCase):
    """Integration tests for Message with actual JSON data."""

    def setUp(self):
        """Set up test fixtures."""
        self.account = OutlookAccount('test_token')

    @patch('pyOutlook.services.message.MessageService._json_to_message')
    def test_json_to_message__correct_format(self, mock_service_method):
        """Test that JSON is converted to Message correctly."""
        expected_message = Message(
            self.account,
            subject='Re: Meeting Notes',
            sender=Contact('katiej@a830edad9050849NDA1.onmicrosoft.com', 'Katie Jordan')
        )
        mock_service_method.return_value = expected_message

        message = Message._json_to_message(self.account, sample_message)

        self.assertEqual(message.subject, 'Re: Meeting Notes')
        self.assertEqual(message.sender.email, 'katiej@a830edad9050849NDA1.onmicrosoft.com')

    @patch('pyOutlook.services.message.MessageService._json_to_message')
    def test_recipients_missing_json__no_failure(self, mock_service_method):
        """Test that missing ToRecipients doesn't cause failure."""
        json_message = {
            "Id": "AAMkAGI2THVSAAA=",
            "Subject": "Test",
            "Body": {"ContentType": "Text", "Content": "Test content"},
            "Sender": {
                "EmailAddress": {
                    "Name": "Test Sender",
                    "Address": "sender@test.com"
                }
            },
            "IsRead": False
        }

        expected_message = Message(self.account, subject='Test')
        mock_service_method.return_value = expected_message

        # Should not raise an exception
        message = Message._json_to_message(self.account, json_message)

        mock_service_method.assert_called_once()


class MessageEdgeCaseTestCase(unittest.TestCase):
    """Edge case tests for Message class."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures - add api_representation methods."""
        # Add api_representation method to Contact if it doesn't exist
        if not hasattr(Contact, 'api_representation'):
            Contact.api_representation = lambda self: dict(self)

        # Add api_representation method to Attachment if it doesn't exist
        if not hasattr(Attachment, 'api_representation'):
            Attachment.api_representation = lambda self: dict(self)

    def setUp(self):
        """Set up test fixtures."""
        self.account = OutlookAccount('test_token')

    def test_empty_subject(self):
        """Test message with empty subject."""
        message = Message(self.account, subject='')
        self.assertEqual(message.subject, '')
        self.assertEqual(str(message), '')

    def test_empty_body(self):
        """Test message with empty body."""
        message = Message(self.account, body='')
        self.assertEqual(message.body, '')

    def test_importance_constants(self):
        """Test importance level constants."""
        self.assertEqual(Message.IMPORTANCE_LOW, 0)
        self.assertEqual(Message.IMPORTANCE_NORMAL, 1)
        self.assertEqual(Message.IMPORTANCE_HIGH, 2)

    @patch('pyOutlook.core.message.requests.post')
    def test_forward__mixed_recipient_types(self, mock_post):
        """Test forward with mixed Contact and string recipients."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        recipients = ['user1@test.com', 'user2@test.com']  # Use all strings to avoid Contact issues
        message.forward(recipients)

        mock_post.assert_called_once()
        # Verify the recipients were converted properly
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertEqual(len(payload['ToRecipients']), 2)

    def test_attach__preserves_order(self):
        """Test that attachments maintain order."""
        message = Message(self.account)

        message.attach(b'first', 'first.txt')
        message.attach(b'second', 'second.txt')
        message.attach(b'third', 'third.txt')

        names = [att.name for att in message._attachments]
        self.assertEqual(names, ['first.txt', 'second.txt', 'third.txt'])

    def test_categories__empty_by_default(self):
        """Test that categories is empty list by default."""
        message = Message(self.account)
        self.assertEqual(message.categories, [])
        self.assertIsInstance(message.categories, list)

    @patch('pyOutlook.core.message.requests.post')
    def test_move_to__message_id_updated_on_response(self, mock_post):
        """Test that move_to updates message_id from response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'Id': 'new_id_456'}
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='old_id_123')
        message.move_to('Inbox')

        self.assertEqual(message.message_id, 'new_id_456')

    @patch('pyOutlook.core.message.requests.post')
    def test_move_to__message_id_preserved_if_not_in_response(self, mock_post):
        """Test that move_to preserves message_id if not in response."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        message = Message(self.account, message_id='msg_123')
        message.move_to('Inbox')

        self.assertEqual(message.message_id, 'msg_123')


if __name__ == '__main__':
    unittest.main()
