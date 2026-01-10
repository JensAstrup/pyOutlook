import unittest
from unittest import mock
from unittest.mock import Mock, MagicMock, patch

import requests

from pyOutlook.services.contact import ContactService
from pyOutlook.core.contact import Contact
from pyOutlook.internal.errors import AuthError, RequestError, APIError


class ContactServiceTestCase(unittest.TestCase):
    """Test cases for ContactService class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_account = Mock()
        self.mock_account._headers = {'Authorization': 'Bearer test_token'}
        self.service = ContactService(self.mock_account)

    def test_init__account_assignment(self):
        """Test that __init__ correctly assigns the account"""
        account = Mock()
        service = ContactService(account)
        self.assertEqual(service.account, account)

    @patch('pyOutlook.services.contact.requests.get')
    @patch('pyOutlook.services.contact.check_response')
    def test_get_overrides__successful_request(self, mock_check_response, mock_get):
        """Test get_overrides with a successful API request"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [
                {
                    'senderEmailAddress': {
                        'name': 'John Doe',
                        'address': 'john@example.com'
                    },
                    'classifyAs': 'Focused'
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        result = self.service.get_overrides()

        # Assert
        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/inferenceClassification/overrides',
            headers=self.mock_account._headers,
            timeout=10
        )
        mock_check_response.assert_called_once_with(mock_response)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Contact)
        self.assertEqual(result[0].email, 'john@example.com')
        self.assertEqual(result[0].name, 'John Doe')
        self.assertTrue(result[0].focused)

    @patch('pyOutlook.services.contact.requests.get')
    @patch('pyOutlook.services.contact.check_response')
    def test_get_overrides__empty_response(self, mock_check_response, mock_get):
        """Test get_overrides with empty API response"""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {'value': []}
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        result = self.service.get_overrides()

        # Assert
        self.assertEqual(result, [])

    @patch('pyOutlook.services.contact.requests.get')
    @patch('pyOutlook.services.contact.check_response')
    def test_get_overrides__check_response_raises_auth_error(self, mock_check_response, mock_get):
        """Test get_overrides when check_response raises AuthError"""
        # Arrange
        mock_response = Mock()
        mock_get.return_value = mock_response
        mock_check_response.side_effect = AuthError('Invalid token')

        # Act & Assert
        with self.assertRaises(AuthError):
            self.service.get_overrides()

    @patch('pyOutlook.services.contact.requests.get')
    @patch('pyOutlook.services.contact.check_response')
    def test_get_overrides__check_response_raises_request_error(self, mock_check_response, mock_get):
        """Test get_overrides when check_response raises RequestError"""
        # Arrange
        mock_response = Mock()
        mock_get.return_value = mock_response
        mock_check_response.side_effect = RequestError('Bad request')

        # Act & Assert
        with self.assertRaises(RequestError):
            self.service.get_overrides()

    @patch('pyOutlook.services.contact.requests.get')
    @patch('pyOutlook.services.contact.check_response')
    def test_get_overrides__check_response_raises_api_error(self, mock_check_response, mock_get):
        """Test get_overrides when check_response raises APIError"""
        # Arrange
        mock_response = Mock()
        mock_get.return_value = mock_response
        mock_check_response.side_effect = APIError('Unknown error')

        # Act & Assert
        with self.assertRaises(APIError):
            self.service.get_overrides()

    def test_json_to_contact__with_email_address_field(self):
        """Test _json_to_contact with standard emailAddress field"""
        # Arrange
        json_data = {
            'emailAddress': {
                'address': 'user@example.com',
                'name': 'Test User'
            }
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.email, 'user@example.com')
        self.assertEqual(result.name, 'Test User')
        self.assertIsNone(result.focused)

    def test_json_to_contact__with_email_address_field_no_name(self):
        """Test _json_to_contact with emailAddress field missing name"""
        # Arrange
        json_data = {
            'emailAddress': {
                'address': 'user@example.com'
            }
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.email, 'user@example.com')
        self.assertIsNone(result.name)
        self.assertIsNone(result.focused)

    def test_json_to_contact__with_email_address_field_no_address(self):
        """Test _json_to_contact with emailAddress field missing address"""
        # Arrange
        json_data = {
            'emailAddress': {
                'name': 'Test User'
            }
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertIsNone(result.email)
        self.assertEqual(result.name, 'Test User')
        self.assertIsNone(result.focused)

    def test_json_to_contact__with_sender_email_address_focused(self):
        """Test _json_to_contact with senderEmailAddress field and Focused classification"""
        # Arrange
        json_data = {
            'senderEmailAddress': {
                'address': 'sender@example.com',
                'name': 'Sender Name'
            },
            'classifyAs': 'Focused'
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.email, 'sender@example.com')
        self.assertEqual(result.name, 'Sender Name')
        self.assertTrue(result.focused)

    def test_json_to_contact__with_sender_email_address_other(self):
        """Test _json_to_contact with senderEmailAddress field and Other classification"""
        # Arrange
        json_data = {
            'senderEmailAddress': {
                'address': 'sender@example.com',
                'name': 'Sender Name'
            },
            'classifyAs': 'Other'
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.email, 'sender@example.com')
        self.assertEqual(result.name, 'Sender Name')
        self.assertFalse(result.focused)

    def test_json_to_contact__with_sender_email_address_no_classification(self):
        """Test _json_to_contact with senderEmailAddress field but no classifyAs"""
        # Arrange
        json_data = {
            'senderEmailAddress': {
                'address': 'sender@example.com',
                'name': 'Sender Name'
            }
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.email, 'sender@example.com')
        self.assertEqual(result.name, 'Sender Name')
        self.assertFalse(result.focused)  # Default is 'Other', which maps to False

    def test_json_to_contact__with_sender_email_address_unknown_classification(self):
        """Test _json_to_contact with senderEmailAddress field and unknown classification"""
        # Arrange
        json_data = {
            'senderEmailAddress': {
                'address': 'sender@example.com',
                'name': 'Sender Name'
            },
            'classifyAs': 'Unknown'
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.email, 'sender@example.com')
        self.assertEqual(result.name, 'Sender Name')
        self.assertFalse(result.focused)  # Not 'Focused' maps to False

    def test_json_to_contact__with_sender_email_address_no_name(self):
        """Test _json_to_contact with senderEmailAddress field missing name"""
        # Arrange
        json_data = {
            'senderEmailAddress': {
                'address': 'sender@example.com'
            },
            'classifyAs': 'Focused'
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.email, 'sender@example.com')
        self.assertIsNone(result.name)
        self.assertTrue(result.focused)

    def test_json_to_contact__with_sender_email_address_no_address(self):
        """Test _json_to_contact with senderEmailAddress field missing address"""
        # Arrange
        json_data = {
            'senderEmailAddress': {
                'name': 'Sender Name'
            },
            'classifyAs': 'Focused'
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsInstance(result, Contact)
        self.assertIsNone(result.email)
        self.assertEqual(result.name, 'Sender Name')
        self.assertTrue(result.focused)

    def test_json_to_contact__neither_email_field_present(self):
        """Test _json_to_contact when neither emailAddress nor senderEmailAddress is present"""
        # Arrange
        json_data = {
            'someOtherField': 'value'
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsNone(result)

    def test_json_to_contact__empty_json(self):
        """Test _json_to_contact with empty JSON object"""
        # Arrange
        json_data = {}

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        self.assertIsNone(result)

    def test_json_to_contacts__single_contact(self):
        """Test _json_to_contacts with a single contact in value array"""
        # Arrange
        json_data = {
            'value': [
                {
                    'emailAddress': {
                        'address': 'user1@example.com',
                        'name': 'User One'
                    }
                }
            ]
        }

        # Act
        result = self.service._json_to_contacts(json_data)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Contact)
        self.assertEqual(result[0].email, 'user1@example.com')
        self.assertEqual(result[0].name, 'User One')

    def test_json_to_contacts__multiple_contacts(self):
        """Test _json_to_contacts with multiple contacts in value array"""
        # Arrange
        json_data = {
            'value': [
                {
                    'emailAddress': {
                        'address': 'user1@example.com',
                        'name': 'User One'
                    }
                },
                {
                    'senderEmailAddress': {
                        'address': 'user2@example.com',
                        'name': 'User Two'
                    },
                    'classifyAs': 'Focused'
                },
                {
                    'emailAddress': {
                        'address': 'user3@example.com',
                        'name': 'User Three'
                    }
                }
            ]
        }

        # Act
        result = self.service._json_to_contacts(json_data)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].email, 'user1@example.com')
        self.assertEqual(result[1].email, 'user2@example.com')
        self.assertTrue(result[1].focused)
        self.assertEqual(result[2].email, 'user3@example.com')

    def test_json_to_contacts__empty_value_array(self):
        """Test _json_to_contacts with empty value array"""
        # Arrange
        json_data = {
            'value': []
        }

        # Act
        result = self.service._json_to_contacts(json_data)

        # Assert
        self.assertEqual(result, [])

    def test_json_to_contacts__contacts_with_none_values(self):
        """Test _json_to_contacts when some contacts return None"""
        # Arrange
        json_data = {
            'value': [
                {
                    'emailAddress': {
                        'address': 'user1@example.com',
                        'name': 'User One'
                    }
                },
                {
                    'invalidField': 'invalid'
                },
                {
                    'emailAddress': {
                        'address': 'user2@example.com',
                        'name': 'User Two'
                    }
                }
            ]
        }

        # Act
        result = self.service._json_to_contacts(json_data)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], Contact)
        self.assertIsNone(result[1])
        self.assertIsInstance(result[2], Contact)

    def test_json_to_contacts__missing_value_key_raises_key_error(self):
        """Test _json_to_contacts raises KeyError when 'value' key is missing"""
        # Arrange
        json_data = {
            'contacts': []
        }

        # Act & Assert
        with self.assertRaises(KeyError):
            self.service._json_to_contacts(json_data)

    def test_json_to_contact__email_address_priority_over_sender(self):
        """Test _json_to_contact prioritizes emailAddress over senderEmailAddress when both present"""
        # Arrange
        json_data = {
            'emailAddress': {
                'address': 'email@example.com',
                'name': 'Email User'
            },
            'senderEmailAddress': {
                'address': 'sender@example.com',
                'name': 'Sender User'
            },
            'classifyAs': 'Focused'
        }

        # Act
        result = self.service._json_to_contact(json_data)

        # Assert
        # Should use emailAddress and ignore senderEmailAddress
        self.assertEqual(result.email, 'email@example.com')
        self.assertEqual(result.name, 'Email User')
        self.assertIsNone(result.focused)  # emailAddress path doesn't set focused


if __name__ == '__main__':
    unittest.main()
