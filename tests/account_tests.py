from unittest import TestCase

from datetime import datetime

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

        with self.assertRaisesRegexp(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('test message', start='not a date', end=datetime.today())

    def test_auto_reply_end_date_must_be_datetime(self):
        account = OutlookAccount('test')

        with self.assertRaisesRegexp(ValueError, 'Start and End must both either be None or datetimes'):
            account.set_auto_reply('test message', start=datetime.today(), end='not a date')

    def test_auto_reply_start_and_end_date_required(self):
        """ Test that a start date and end date must be given together """
        account = OutlookAccount('123')

        with self.assertRaisesRegexp(ValueError, "Start and End not must both either be None or datetimes"):
            account.set_auto_reply('message', start=datetime.today())

        with self.assertRaisesRegexp(ValueError, "Start and End not must both either be None or datetimes"):
            account.set_auto_reply('message', end=datetime.today())