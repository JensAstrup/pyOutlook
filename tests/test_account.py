from datetime import datetime
from unittest import TestCase, mock

from pyOutlook import *


class TestAccount(TestCase):

    def test_account_requires_token(self):
        """ Test that an account cannot be created without an access token """
        with self.assertRaises(TypeError):
            OutlookAccount()

    def test_headers(self):
        """ Test that headers contain the access token and the default content type only."""
        account = OutlookAccount('token123')
        headers = account._headers

        self.assertIn('Authorization', headers)
        auth = headers.pop('Authorization')
        self.assertEqual('Bearer {}'.format('token123'), auth)

        self.assertIn('Content-Type', headers)
        content_type = headers.pop('Content-Type')
        self.assertEqual('application/json', content_type)

        # There should be nothing left in the headers
        self.assertFalse(bool(headers))

    def test_auto_reply_start_date_must_be_datetime(self):
        account = OutlookAccount('test')

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('test message', start='not a date', end=datetime.today())

    def test_auto_reply_end_date_must_be_datetime(self):
        account = OutlookAccount('test')

        with self.assertRaisesRegex(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('test message', start=datetime.today(), end='not a date')

    def test_auto_reply_start_and_end_date_required(self):
        """ Test that a start date and end date must be given together """
        account = OutlookAccount('123')

        with self.assertRaisesRegex(ValueError, "Start and End must both either be None or datetimes"):
            account.set_auto_reply('message', start=datetime.today())

        with self.assertRaisesRegex(ValueError, "Start and End must both either be None or datetimes"):
            account.set_auto_reply('message', end=datetime.today())

    @mock.patch.object(Message, '__init__')
    def test_new_email(self, message_init):
        message_init.return_value = None
        account = OutlookAccount('token')
        body = 'Test Body'
        subject = 'My Subject'
        to = ['some_dude@email.com']
        account.new_email(body, subject, to)
        message_init.assert_called_once_with(account, body, subject, to)

    @mock.patch.object(Message, 'send')
    @mock.patch.object(Message, '__init__')
    def test_send_email(self, message_init, send):
        message_init.return_value = None
        account = OutlookAccount('token')
        body = 'Test Body'
        subject = 'Test Subject'
        to = ['dude@email.com']
        account.send_email(body, subject, to)
        message_init.assert_called_once_with(account, body, subject, to, bcc=None, cc=None, sender=None)
        send.assert_called_once()