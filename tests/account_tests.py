from unittest import TestCase

from pyOutlook import *


class TestAccount(TestCase):

    def test_account_requires_token(self):
        """ Test that an account cannot be created without an access token """
        with self.assertRaises(TypeError):
            OutlookAccount()

    def test_headers(self):
        """ Test that headers contain the access token and the default content type only."""
        account = OutlookAccount('token123')
        headers = account.headers

        self.assertIn('Authorization', headers)
        auth = headers.pop('Authorization')
        self.assertEqual('Bearer {}'.format('token123'), auth)

        self.assertIn('Content-Type', headers)
        content_type = headers.pop('Content-Type')
        self.assertEqual('application/json', content_type)

        # There should be nothing left in the headers
        self.assertFalse(bool(headers))
