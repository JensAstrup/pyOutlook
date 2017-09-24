import base64
from unittest import TestCase

try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import Mock, patch

from pyOutlook import OutlookAccount
from pyOutlook.core.contact import Contact
from pyOutlook.core.message import Message
from tests.utils import sample_message


class TestMessage(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock_get_patcher = patch('pyOutlook.core.message.requests.get')
        cls.mock_get = cls.mock_get_patcher.start()

        cls.mock_patch_patcher = patch('pyOutlook.core.message.requests.patch')
        cls.mock_patch = cls.mock_patch_patcher.start()

        cls.mock_post_patcher = patch('pyOutlook.core.message.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()

        cls.account = OutlookAccount('token')

    def test_json_to_message_format(self):
        """ Test that JSON is turned into a Message correctly """
        mock_response = Mock()
        mock_response.json.return_value = sample_message
        mock_response.status_code = 200

        self.mock_get.return_value = mock_response

        account = OutlookAccount('token')

        message = Message._json_to_message(account, sample_message)

        self.assertEqual(message.subject, 'Re: Meeting Notes')

        sender = Contact('katiej@a830edad9050849NDA1.onmicrosoft.com', 'Katie Jordan')

        self.assertIsInstance(message.sender, Contact)
        self.assertEqual(message.sender.email, sender.email)
        self.assertEqual(message.sender.name, sender.name)

    def test_recipients_missing_json(self):
        """ Test that a response with no ToRecipients does not cause Message deserialization to fail """
        json_message = {
            "Id": "AAMkAGI2THVSAAA=",
            "CreatedDateTime": "2014-10-20T00:41:57Z",
            "LastModifiedDateTime": "2014-10-20T00:41:57Z",
            "ReceivedDateTime": "2014-10-20T00:41:57Z",
            "SentDateTime": "2014-10-20T00:41:53Z",
            "Subject": "Re: Meeting Notes",
            "Body": {
                "ContentType": "Text",
                "Content": "\n\nFrom: Alex D\nSent: Sunday, October 19, 2014 5:28 PM\nTo: Katie Jordan\nSubject: "
                           "Meeting Notes\n\nPlease send me the meeting notes ASAP\n"
            },
            "BodyPreview": "\nFrom: Alex D\nSent: Sunday, October 19, 2014 5:28 PM\nTo: Katie Jordan\n"
                           "Subject: Meeting Notes\n\nPlease send me the meeting notes ASAP",
            "Sender": {
                "EmailAddress": {
                    "Name": "Katie Jordan",
                    "Address": "katiej@a830edad9050849NDA1.onmicrosoft.com"
                }
            },
            "From": {
                "EmailAddress": {
                    "Name": "Katie Jordan",
                    "Address": "katiej@a830edad9050849NDA1.onmicrosoft.com"
                }
            },
            "CcRecipients": [],
            "BccRecipients": [],
            "ReplyTo": [],
            "ConversationId": "AAQkAGI2yEto=",
            "IsRead": False,
            'HasAttachments': True
        }
        Message._json_to_message(self.account, json_message)

    def test_is_read_status(self):
        """ Test that the correct value is returned after changing the is_read status """
        mock_patch = Mock()
        mock_patch.status_code = 200

        self.mock_patch.return_value = mock_patch

        message = Message(self.account, 'test body', 'test subject', [], is_read=False)
        message.is_read = True

        self.assertTrue(message.is_read)

    def test_attachments_added(self):
        """ Test that attachments are added to Message in the correct format """
        message = Message(self.account, '', '', [])

        message.attach('abc', 'Test/Attachment.csv')
        message.attach(b'some bytes', 'attached.pdf')

        self.assertEqual(len(message._attachments), 2)
        file_bytes = [attachment._content for attachment in message._attachments]
        file_names = [attachment.name for attachment in message._attachments]

        # The files are base64'd for the API
        some_bytes = base64.b64encode(b'some bytes')
        abc = base64.b64encode(b'abc')

        self.assertIn(some_bytes.decode('UTF-8'), file_bytes)
        self.assertIn(abc.decode('UTF-8'), file_bytes)
        self.assertIn('TestAttachment.csv', file_names)

    def test_message_sent_with_string_recipients(self):
        """ A list of strings or Contacts can be provided as the To/CC/BCC recipients """
        mock_post = Mock()
        mock_post.status_code = 200
        self.mock_post.return_value = mock_post

        message = Message(self.account, '', '', ['test@email.com'])
        message.send()

    def test_message_sent_with_contact_recipients(self):
        """ A list of strings or Contacts can be provided as the To/CC/BCC recipients """
        mock_post = Mock()
        mock_post.status_code = 200
        self.mock_post.return_value = mock_post

        message = Message(self.account, '', '', [Contact('test@email.com')])
        message.send()

    def test_category_added(self):
        """ Test that Message.categories is updated in addition to the API call made """
        mock_patch = Mock()
        mock_patch.status_code = 200

        self.mock_patch.return_value = mock_patch

        message = Message(self.account, 'test body', 'test subject', [], categories=['A'])
        message.add_category('B')

        self.assertIn('A', message.categories)
        self.assertIn('B', message.categories)
