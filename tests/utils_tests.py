from unittest import TestCase

try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import Mock, patch

from pyOutlook import *
from pyOutlook.internal.utils import check_response
from pyOutlook.internal.errors import AuthError, RequestError, APIError


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

    def test_401_response(self):
        """ Test that an AuthError is raised """
        mock = Mock()
        mock.status_code = 401

        with self.assertRaises(AuthError):
            check_response(mock)

    def test_403_response(self):
        """ Test that an AuthError is raised """
        mock = Mock()
        mock.status_code = 403

        with self.assertRaises(AuthError):
            check_response(mock)

    def test_500_response(self):
        """ Test that an APIError is raised """
        mock = Mock()
        mock.status_code = 500

        with self.assertRaises(APIError):
            check_response(mock)

    def test_400_response(self):
        """ Test that a RequestError is raised """
        mock = Mock()
        mock.status_code = 400

        with self.assertRaises(RequestError):
            check_response(mock)

    def test_405_response(self):
        """ Test that an APIError is raised """
        mock = Mock()
        mock.status_code = 500

        with self.assertRaises(APIError):
            check_response(mock)