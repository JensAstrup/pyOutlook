import json
from unittest import TestCase

try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import Mock, patch

from pyOutlook import OutlookAccount
from pyOutlook.core.contact import Contact
from pyOutlook.internal.errors import AuthError, RequestError, APIError


class ContactTestCase(TestCase):
    """Test suite for the Contact class"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are reused across test methods"""
        cls.mock_post_patcher = patch('pyOutlook.core.contact.requests.post')
        cls.mock_post = cls.mock_post_patcher.start()
        cls.account = OutlookAccount('test_token')

    @classmethod
    def tearDownClass(cls):
        """Clean up patchers after all tests"""
        cls.mock_post_patcher.stop()

    def setUp(self):
        """Reset mocks before each test"""
        self.mock_post.reset_mock()


class ContactInitTestCase(ContactTestCase):
    """Test cases for Contact.__init__"""

    def test_init__with_email_only(self):
        """Test Contact initialization with only email parameter"""
        contact = Contact('test@example.com')

        self.assertEqual(contact.email, 'test@example.com')
        self.assertIsNone(contact.name)
        self.assertIsNone(contact.focused)

    def test_init__with_email_and_name(self):
        """Test Contact initialization with email and name parameters"""
        contact = Contact('test@example.com', 'Test User')

        self.assertEqual(contact.email, 'test@example.com')
        self.assertEqual(contact.name, 'Test User')
        self.assertIsNone(contact.focused)

    def test_init__with_all_parameters(self):
        """Test Contact initialization with all parameters including focused"""
        contact = Contact('test@example.com', 'Test User', True)

        self.assertEqual(contact.email, 'test@example.com')
        self.assertEqual(contact.name, 'Test User')
        self.assertTrue(contact.focused)

    def test_init__with_focused_false(self):
        """Test Contact initialization with focused set to False"""
        contact = Contact('test@example.com', 'Test User', False)

        self.assertEqual(contact.email, 'test@example.com')
        self.assertEqual(contact.name, 'Test User')
        self.assertFalse(contact.focused)

    def test_init__with_focused_keyword_arg(self):
        """Test Contact initialization using focused as keyword argument"""
        contact = Contact('test@example.com', focused=True)

        self.assertEqual(contact.email, 'test@example.com')
        self.assertIsNone(contact.name)
        self.assertTrue(contact.focused)


class ContactStrTestCase(ContactTestCase):
    """Test cases for Contact.__str__"""

    def test_str__name_is_none(self):
        """Test __str__ returns only email when name is None"""
        contact = Contact('test@example.com')

        result = str(contact)

        self.assertEqual(result, 'test@example.com')

    def test_str__name_is_provided(self):
        """Test __str__ returns formatted string when name is provided"""
        contact = Contact('test@example.com', 'Test User')

        result = str(contact)

        self.assertEqual(result, 'Test User (test@example.com)')

    def test_str__name_is_empty_string(self):
        """Test __str__ returns formatted string when name is empty string"""
        contact = Contact('test@example.com', '')

        result = str(contact)

        self.assertEqual(result, ' (test@example.com)')


class ContactReprTestCase(ContactTestCase):
    """Test cases for Contact.__repr__"""

    def test_repr__name_is_none(self):
        """Test __repr__ returns str representation when name is None"""
        contact = Contact('test@example.com')

        result = repr(contact)

        self.assertEqual(result, 'test@example.com')

    def test_repr__name_is_provided(self):
        """Test __repr__ returns str representation when name is provided"""
        contact = Contact('test@example.com', 'Test User')

        result = repr(contact)

        self.assertEqual(result, 'Test User (test@example.com)')


class ContactIterTestCase(ContactTestCase):
    """Test cases for Contact.__iter__"""

    def test_iter__with_name_and_email(self):
        """Test __iter__ yields correct API-formatted dictionary with name"""
        contact = Contact('test@example.com', 'Test User')

        result = dict(contact)

        expected = {
            'EmailAddress': {
                'Name': 'Test User',
                'Address': 'test@example.com'
            }
        }
        self.assertEqual(result, expected)

    def test_iter__with_email_only(self):
        """Test __iter__ yields correct API-formatted dictionary without name"""
        contact = Contact('test@example.com')

        result = dict(contact)

        expected = {
            'EmailAddress': {
                'Name': None,
                'Address': 'test@example.com'
            }
        }
        self.assertEqual(result, expected)

    def test_iter__preserves_focused_attribute(self):
        """Test __iter__ does not modify focused attribute"""
        contact = Contact('test@example.com', 'Test User', True)

        dict(contact)

        self.assertTrue(contact.focused)


class ContactSetFocusedTestCase(ContactTestCase):
    """Test cases for Contact.set_focused"""

    def test_set_focused__is_focused_true(self):
        """Test set_focused with is_focused=True sends correct classification"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com', 'Test User')
        result = contact.set_focused(self.account, True)

        # Verify the request was made
        self.assertTrue(self.mock_post.called)

        # Verify the endpoint
        call_args = self.mock_post.call_args
        self.assertEqual(
            call_args[0][0],
            'https://graph.microsoft.com/v1.0/me/InferenceClassification/Overrides'
        )

        # Verify the data payload
        sent_data = json.loads(call_args[1]['data'])
        expected_data = {
            'ClassifyAs': 'Focused',
            'SenderEmailAddress': {
                'Address': 'test@example.com'
            }
        }
        self.assertEqual(sent_data, expected_data)

        # Verify timeout is set
        self.assertEqual(call_args[1]['timeout'], 10)

        # Verify focused attribute is updated
        self.assertTrue(contact.focused)

        # Verify return value
        self.assertTrue(result)

    def test_set_focused__is_focused_false(self):
        """Test set_focused with is_focused=False sends correct classification"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com', 'Test User')
        result = contact.set_focused(self.account, False)

        # Verify the request was made
        self.assertTrue(self.mock_post.called)

        # Verify the data payload
        call_args = self.mock_post.call_args
        sent_data = json.loads(call_args[1]['data'])
        expected_data = {
            'ClassifyAs': 'Other',
            'SenderEmailAddress': {
                'Address': 'test@example.com'
            }
        }
        self.assertEqual(sent_data, expected_data)

        # Verify focused attribute is updated
        self.assertFalse(contact.focused)

        # Verify return value
        self.assertTrue(result)

    def test_set_focused__updates_existing_focused_true_to_false(self):
        """Test set_focused correctly updates focused from True to False"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com', 'Test User', focused=True)
        contact.set_focused(self.account, False)

        self.assertFalse(contact.focused)

    def test_set_focused__updates_existing_focused_false_to_true(self):
        """Test set_focused correctly updates focused from False to True"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com', 'Test User', focused=False)
        contact.set_focused(self.account, True)

        self.assertTrue(contact.focused)

    def test_set_focused__uses_account_headers(self):
        """Test set_focused uses the account's headers in the request"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')
        contact.set_focused(self.account, True)

        call_args = self.mock_post.call_args
        self.assertEqual(call_args[1]['headers'], self.account._headers)

    def test_set_focused__successful_201_response(self):
        """Test set_focused handles 201 Created response successfully"""
        mock_response = Mock()
        mock_response.status_code = 201
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')
        result = contact.set_focused(self.account, True)

        self.assertTrue(result)
        self.assertTrue(contact.focused)

    def test_set_focused__successful_298_response(self):
        """Test set_focused handles upper boundary 298 response successfully"""
        mock_response = Mock()
        mock_response.status_code = 298
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')
        result = contact.set_focused(self.account, True)

        self.assertTrue(result)
        self.assertTrue(contact.focused)

    def test_set_focused__401_raises_auth_error(self):
        """Test set_focused raises AuthError on 401 response"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'Unauthorized'}
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')

        with self.assertRaises(AuthError):
            contact.set_focused(self.account, True)

    def test_set_focused__403_raises_auth_error(self):
        """Test set_focused raises AuthError on 403 response"""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.json.return_value = {'error': 'Forbidden'}
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')

        with self.assertRaises(AuthError):
            contact.set_focused(self.account, True)

    def test_set_focused__400_raises_request_error(self):
        """Test set_focused raises RequestError on 400 response"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Bad Request'}
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')

        with self.assertRaises(RequestError):
            contact.set_focused(self.account, True)

    def test_set_focused__500_raises_api_error(self):
        """Test set_focused raises APIError on 500 response"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'error': 'Internal Server Error'}
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')

        with self.assertRaises(APIError):
            contact.set_focused(self.account, True)

    def test_set_focused__404_raises_api_error(self):
        """Test set_focused raises APIError on 404 response"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'error': 'Not Found'}
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')

        with self.assertRaises(APIError):
            contact.set_focused(self.account, True)

    def test_set_focused__does_not_update_focused_on_error(self):
        """Test set_focused does not update focused attribute when request fails"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'error': 'Bad Request'}
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com', focused=None)

        with self.assertRaises(RequestError):
            contact.set_focused(self.account, True)

        # Focused should remain None since the request failed
        self.assertIsNone(contact.focused)

    def test_set_focused__with_contact_without_name(self):
        """Test set_focused works correctly when contact has no name"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com')
        result = contact.set_focused(self.account, True)

        # Verify the data payload
        call_args = self.mock_post.call_args
        sent_data = json.loads(call_args[1]['data'])
        expected_data = {
            'ClassifyAs': 'Focused',
            'SenderEmailAddress': {
                'Address': 'test@example.com'
            }
        }
        self.assertEqual(sent_data, expected_data)
        self.assertTrue(result)


class ContactIntegrationTestCase(ContactTestCase):
    """Integration test cases for Contact class"""

    def test_contact__full_workflow_focused_true(self):
        """Test complete workflow: create contact, set focused to True"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        # Create contact
        contact = Contact('workflow@example.com', 'Workflow User')
        self.assertIsNone(contact.focused)

        # Set to focused
        result = contact.set_focused(self.account, True)

        self.assertTrue(result)
        self.assertTrue(contact.focused)
        self.assertEqual(str(contact), 'Workflow User (workflow@example.com)')

    def test_contact__full_workflow_focused_false(self):
        """Test complete workflow: create contact, set focused to False"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        # Create contact
        contact = Contact('workflow@example.com', 'Workflow User')
        self.assertIsNone(contact.focused)

        # Set to other
        result = contact.set_focused(self.account, False)

        self.assertTrue(result)
        self.assertFalse(contact.focused)
        self.assertEqual(str(contact), 'Workflow User (workflow@example.com)')

    def test_contact__dict_conversion_after_set_focused(self):
        """Test that dict conversion still works after set_focused"""
        mock_response = Mock()
        mock_response.status_code = 200
        self.mock_post.return_value = mock_response

        contact = Contact('test@example.com', 'Test User')
        contact.set_focused(self.account, True)

        result = dict(contact)

        expected = {
            'EmailAddress': {
                'Name': 'Test User',
                'Address': 'test@example.com'
            }
        }
        self.assertEqual(result, expected)
        # Verify focused is still set
        self.assertTrue(contact.focused)
