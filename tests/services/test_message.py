import json
import unittest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from pyOutlook.core.main import OutlookAccount
from pyOutlook.core.message import Message
from pyOutlook.core.contact import Contact
from pyOutlook.core.attachment import Attachment
from pyOutlook.services.message import MessageService
from pyOutlook.internal.errors import AuthError, RequestError, APIError


# Monkey-patch Contact to add api_representation method that doesn't exist in current version
# This allows testing the MessageService code that calls this method
def _contact_api_representation(self):
    """Returns the JSON formatting required by Outlook's API for contacts"""
    return dict(EmailAddress=dict(Name=self.name, Address=self.email))


Contact.api_representation = _contact_api_representation


# Monkey-patch Attachment to add api_representation method if it doesn't exist
def _attachment_api_representation(self):
    """Returns the JSON formatting required by Outlook's API for attachments"""
    return dict(self)


Attachment.api_representation = _attachment_api_representation


class MessageServiceTestCase(unittest.TestCase):
    """Test cases for MessageService class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_account = Mock(spec=OutlookAccount)
        self.mock_account._headers = {
            'Authorization': 'Bearer test_token',
            'Content-Type': 'application/json'
        }
        self.service = MessageService(self.mock_account)

    def test_init__creates_service_with_account(self):
        """Test MessageService initialization with account"""
        service = MessageService(self.mock_account)
        self.assertEqual(service.account, self.mock_account)

    @patch('pyOutlook.services.message.requests.get')
    @patch('pyOutlook.services.message.check_response')
    def test_get__successful_retrieval(self, mock_check_response, mock_get):
        """Test get method successfully retrieves a single message"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'message123',
            'subject': 'Test Subject',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com',
                    'name': 'Sender Name'
                }
            },
            'body': {'content': 'Test body'},
            'bodyPreview': 'Test preview',
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': 'recipient@example.com',
                        'name': 'Recipient Name'
                    }
                }
            ],
            'isRead': True,
            'hasAttachments': False
        }
        mock_get.return_value = mock_response

        result = self.service.get('message123')

        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/messages/message123',
            headers=self.mock_account._headers,
            timeout=10
        )
        mock_check_response.assert_called_once_with(mock_response)
        self.assertIsInstance(result, Message)
        self.assertEqual(result.subject, 'Test Subject')

    @patch('pyOutlook.services.message.requests.get')
    @patch('pyOutlook.services.message.check_response')
    def test_all__page_zero(self, mock_check_response, mock_get):
        """Test all method with page=0 (default)"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [
                {
                    'id': 'msg1',
                    'subject': 'Message 1',
                    'sender': {
                        'emailAddress': {
                            'address': 'sender1@example.com'
                        }
                    },
                    'body': {'content': 'Body 1'},
                    'toRecipients': [],
                    'isRead': False,
                    'hasAttachments': False
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.service.all(page=0)

        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/messages',
            headers=self.mock_account._headers,
            timeout=10
        )
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Message)

    @patch('pyOutlook.services.message.requests.get')
    @patch('pyOutlook.services.message.check_response')
    def test_all__page_greater_than_zero(self, mock_check_response, mock_get):
        """Test all method with page > 0"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.json.return_value = {'value': []}
        mock_get.return_value = mock_response

        result = self.service.all(page=2)

        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/messages/?%24skip=20',
            headers=self.mock_account._headers,
            timeout=10
        )
        self.assertEqual(len(result), 0)

    @patch('pyOutlook.services.message.requests.get')
    @patch('pyOutlook.services.message.check_response')
    def test_from_folder__successful_retrieval(self, mock_check_response, mock_get):
        """Test from_folder method retrieves messages from specific folder"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [
                {
                    'id': 'inbox_msg1',
                    'subject': 'Inbox Message',
                    'sender': {
                        'emailAddress': {
                            'address': 'sender@example.com'
                        }
                    },
                    'body': {'content': 'Inbox body'},
                    'toRecipients': [],
                    'isRead': True,
                    'hasAttachments': False
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.service.from_folder('Inbox')

        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages',
            headers=self.mock_account._headers,
            timeout=10
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].subject, 'Inbox Message')

    def test_json_to_messages__multiple_messages(self):
        """Test _json_to_messages converts array of messages"""
        json_data = {
            'value': [
                {
                    'id': 'msg1',
                    'subject': 'Subject 1',
                    'sender': {
                        'emailAddress': {
                            'address': 'sender1@example.com'
                        }
                    },
                    'body': {'content': 'Body 1'},
                    'toRecipients': [],
                    'isRead': False,
                    'hasAttachments': False
                },
                {
                    'id': 'msg2',
                    'subject': 'Subject 2',
                    'sender': {
                        'emailAddress': {
                            'address': 'sender2@example.com'
                        }
                    },
                    'body': {'content': 'Body 2'},
                    'toRecipients': [],
                    'isRead': True,
                    'hasAttachments': False
                }
            ]
        }

        result = self.service._json_to_messages(json_data)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].subject, 'Subject 1')
        self.assertEqual(result[1].subject, 'Subject 2')

    def test_json_to_messages__empty_array(self):
        """Test _json_to_messages handles empty array"""
        json_data = {'value': []}

        result = self.service._json_to_messages(json_data)

        self.assertEqual(len(result), 0)

    def test_json_to_message__complete_message(self):
        """Test _json_to_message with all fields populated"""
        api_json = {
            'id': 'message123',
            'subject': 'Complete Message',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com',
                    'name': 'Sender Name'
                }
            },
            'body': {
                'content': '<html>Body content</html>'
            },
            'bodyPreview': 'Body preview text',
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': 'recipient1@example.com',
                        'name': 'Recipient One'
                    }
                },
                {
                    'emailAddress': {
                        'address': 'recipient2@example.com',
                        'name': 'Recipient Two'
                    }
                }
            ],
            'isRead': True,
            'hasAttachments': True,
            'createdDateTime': '2024-01-15T10:30:00Z',
            'SentDateTime': '2024-01-15T10:35:00Z',
            'ParentFolderId': 'folder123',
            'IsDraft': False,
            'Importance': 'High',
            'Categories': ['Important', 'Work'],
            'InferenceClassification': 'Focused'
        }

        result = self.service._json_to_message(api_json)

        self.assertIsInstance(result, Message)
        self.assertEqual(result.message_id, 'message123')
        self.assertEqual(result.subject, 'Complete Message')
        self.assertEqual(result.sender.email, 'sender@example.com')
        self.assertEqual(result.body, '<html>Body content</html>')
        self.assertEqual(result.body_preview, 'Body preview text')
        self.assertEqual(len(result.to), 2)
        self.assertEqual(result.to[0].email, 'recipient1@example.com')
        self.assertTrue(result.is_read)
        self.assertTrue(result._has_attachments)
        self.assertIsInstance(result.time_created, datetime)
        self.assertIsInstance(result.time_sent, datetime)
        self.assertEqual(result.parent_folder_id, 'folder123')
        self.assertFalse(result.is_draft)
        self.assertEqual(result.importance, 'High')
        self.assertEqual(result.categories, ['Important', 'Work'])
        self.assertTrue(result.focused)

    def test_json_to_message__minimal_message(self):
        """Test _json_to_message with minimal required fields"""
        api_json = {
            'id': 'minimal_msg',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': False,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(result.message_id, 'minimal_msg')
        self.assertEqual(result.subject, '')
        self.assertEqual(result.sender.email, 'sender@example.com')
        self.assertEqual(result.body, '')
        self.assertEqual(result.body_preview, '')
        self.assertEqual(len(result.to), 0)
        self.assertFalse(result.is_read)
        self.assertFalse(result._has_attachments)

    def test_json_to_message__missing_subject(self):
        """Test _json_to_message with missing subject field"""
        api_json = {
            'id': 'msg123',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(result.subject, '')

    def test_json_to_message__missing_body(self):
        """Test _json_to_message with missing body field"""
        api_json = {
            'id': 'msg123',
            'subject': 'No Body',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(result.body, '')

    def test_json_to_message__missing_body_preview(self):
        """Test _json_to_message with missing bodyPreview field"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'body': {'content': 'Test body'},
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(result.body_preview, '')

    def test_json_to_message__missing_to_recipients(self):
        """Test _json_to_message with missing toRecipients field"""
        api_json = {
            'id': 'msg123',
            'subject': 'No Recipients',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'body': {'content': 'Test'},
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(len(result.to), 0)

    def test_json_to_message__empty_to_recipients(self):
        """Test _json_to_message with empty toRecipients array"""
        api_json = {
            'id': 'msg123',
            'subject': 'Empty Recipients',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'body': {'content': 'Test'},
            'toRecipients': [],
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(len(result.to), 0)

    def test_json_to_message__no_created_datetime(self):
        """Test _json_to_message with missing createdDateTime"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertIsNone(result.time_created)

    def test_json_to_message__with_created_datetime(self):
        """Test _json_to_message parses createdDateTime correctly"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'createdDateTime': '2024-01-15T10:30:00.000Z',
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertIsInstance(result.time_created, datetime)
        self.assertEqual(result.time_created.year, 2024)
        self.assertEqual(result.time_created.month, 1)
        self.assertEqual(result.time_created.day, 15)

    def test_json_to_message__no_sent_datetime(self):
        """Test _json_to_message with missing SentDateTime"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertIsNone(result.time_sent)

    def test_json_to_message__with_sent_datetime(self):
        """Test _json_to_message parses SentDateTime correctly"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'SentDateTime': '2024-01-15T11:00:00.000Z',
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertIsInstance(result.time_sent, datetime)
        self.assertEqual(result.time_sent.hour, 11)

    def test_json_to_message__no_parent_folder_id(self):
        """Test _json_to_message with missing ParentFolderId"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertIsNone(result.parent_folder_id)

    def test_json_to_message__no_is_draft(self):
        """Test _json_to_message with missing IsDraft"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertIsNone(result.is_draft)

    def test_json_to_message__no_importance_defaults_to_normal(self):
        """Test _json_to_message defaults to IMPORTANCE_NORMAL when missing"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(result.importance, Message.IMPORTANCE_NORMAL)

    def test_json_to_message__no_categories_defaults_to_empty_list(self):
        """Test _json_to_message defaults to empty list when Categories missing"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertEqual(result.categories, [])

    def test_json_to_message__inference_classification_focused(self):
        """Test _json_to_message sets focused=True for Focused classification"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'InferenceClassification': 'Focused',
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertTrue(result.focused)

    def test_json_to_message__inference_classification_other(self):
        """Test _json_to_message sets focused=False for Other classification"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'InferenceClassification': 'Other',
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertFalse(result.focused)

    def test_json_to_message__inference_classification_missing_defaults_to_other(self):
        """Test _json_to_message defaults to Other (focused=False) when missing"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        self.assertFalse(result.focused)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__with_to_recipients_only(self, mock_check_response, mock_post):
        """Test send method with only to recipients"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com', 'Recipient Name')]

        self.service.send('Test Subject', '<html>Test Body</html>', to)

        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # Verify endpoint
        self.assertEqual(call_args[0][0], 'https://graph.microsoft.com/v1.0/me/sendMail')

        # Verify headers
        self.assertEqual(call_args[1]['headers'], self.mock_account._headers)

        # Verify timeout
        self.assertEqual(call_args[1]['timeout'], 10)

        # Verify payload
        payload = json.loads(call_args[1]['data'])
        message = payload['message']
        self.assertEqual(message['subject'], 'Test Subject')
        self.assertEqual(message['body']['contentType'], 'HTML')
        self.assertEqual(message['body']['content'], '<html>Test Body</html>')
        self.assertEqual(len(message['toRecipients']), 1)
        self.assertNotIn('ccRecipients', message)
        self.assertNotIn('bccRecipients', message)
        self.assertNotIn('attachments', message)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__with_cc_recipients(self, mock_check_response, mock_post):
        """Test send method with CC recipients"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]
        cc = [Contact('cc1@example.com'), Contact('cc2@example.com')]

        self.service.send('Test Subject', 'Test Body', to, cc=cc)

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertEqual(len(message['ccRecipients']), 2)
        self.assertEqual(message['ccRecipients'][0]['EmailAddress']['Address'], 'cc1@example.com')

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__with_bcc_recipients(self, mock_check_response, mock_post):
        """Test send method with BCC recipients"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]
        bcc = [Contact('bcc@example.com')]

        self.service.send('Test Subject', 'Test Body', to, bcc=bcc)

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertEqual(len(message['bccRecipients']), 1)
        self.assertEqual(message['bccRecipients'][0]['EmailAddress']['Address'], 'bcc@example.com')

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__with_attachments(self, mock_check_response, mock_post):
        """Test send method with attachments"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]
        attachment = Attachment('test.txt', 'dGVzdCBjb250ZW50', content_type='text/plain')

        self.service.send('Test Subject', 'Test Body', to, attachments=[attachment])

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertIn('attachments', message)
        self.assertEqual(len(message['attachments']), 1)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__with_all_parameters(self, mock_check_response, mock_post):
        """Test send method with all parameters"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('to@example.com')]
        cc = [Contact('cc@example.com')]
        bcc = [Contact('bcc@example.com')]
        attachment = Attachment('file.pdf', 'cGRmIGNvbnRlbnQ=', content_type='application/pdf')

        self.service.send('Subject', 'Body', to, cc=cc, bcc=bcc, attachments=[attachment])

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertIn('toRecipients', message)
        self.assertIn('ccRecipients', message)
        self.assertIn('bccRecipients', message)
        self.assertIn('attachments', message)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__none_cc_recipients(self, mock_check_response, mock_post):
        """Test send method with None CC recipients"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]

        self.service.send('Test Subject', 'Test Body', to, cc=None)

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertNotIn('ccRecipients', message)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__none_bcc_recipients(self, mock_check_response, mock_post):
        """Test send method with None BCC recipients"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]

        self.service.send('Test Subject', 'Test Body', to, bcc=None)

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertNotIn('bccRecipients', message)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__none_attachments(self, mock_check_response, mock_post):
        """Test send method with None attachments"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]

        self.service.send('Test Subject', 'Test Body', to, attachments=None)

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertNotIn('attachments', message)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__empty_cc_list(self, mock_check_response, mock_post):
        """Test send method with empty CC list"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]

        self.service.send('Test Subject', 'Test Body', to, cc=[])

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertNotIn('ccRecipients', message)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__empty_bcc_list(self, mock_check_response, mock_post):
        """Test send method with empty BCC list"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]

        self.service.send('Test Subject', 'Test Body', to, bcc=[])

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertNotIn('bccRecipients', message)

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__empty_attachments_list(self, mock_check_response, mock_post):
        """Test send method with empty attachments list"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('recipient@example.com')]

        self.service.send('Test Subject', 'Test Body', to, attachments=[])

        payload = json.loads(mock_post.call_args[1]['data'])
        message = payload['message']
        self.assertNotIn('attachments', message)

    @patch('pyOutlook.services.message.requests.get')
    @patch('pyOutlook.services.message.check_response')
    def test_get__check_response_called(self, mock_check_response, mock_get):
        """Test get method calls check_response for error handling"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'msg123',
            'sender': {'emailAddress': {'address': 'test@example.com'}},
            'isRead': True,
            'hasAttachments': False
        }
        mock_get.return_value = mock_response

        self.service.get('msg123')

        mock_check_response.assert_called_once()

    @patch('pyOutlook.services.message.requests.get')
    @patch('pyOutlook.services.message.check_response')
    def test_all__check_response_called(self, mock_check_response, mock_get):
        """Test all method calls check_response for error handling"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.json.return_value = {'value': []}
        mock_get.return_value = mock_response

        self.service.all()

        mock_check_response.assert_called_once()

    @patch('pyOutlook.services.message.requests.get')
    @patch('pyOutlook.services.message.check_response')
    def test_from_folder__check_response_called(self, mock_check_response, mock_get):
        """Test from_folder method calls check_response for error handling"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.json.return_value = {'value': []}
        mock_get.return_value = mock_response

        self.service.from_folder('Inbox')

        mock_check_response.assert_called_once()

    @patch('pyOutlook.services.message.requests.post')
    @patch('pyOutlook.services.message.check_response')
    def test_send__check_response_called(self, mock_check_response, mock_post):
        """Test send method calls check_response for error handling"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        to = [Contact('test@example.com')]
        self.service.send('Subject', 'Body', to)

        mock_check_response.assert_called_once()

    def test_json_to_message__filters_none_contacts(self):
        """Test _json_to_message filters out None values from to_recipients"""
        api_json = {
            'id': 'msg123',
            'subject': 'Test',
            'sender': {
                'emailAddress': {
                    'address': 'sender@example.com'
                }
            },
            'toRecipients': [
                {
                    'emailAddress': {
                        'address': 'valid@example.com'
                    }
                }
            ],
            'isRead': True,
            'hasAttachments': False
        }

        result = self.service._json_to_message(api_json)

        # Verify all contacts are not None
        self.assertTrue(all(contact is not None for contact in result.to))


if __name__ == '__main__':
    unittest.main()
