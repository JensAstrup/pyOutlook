import json
import unittest
from unittest.mock import patch, Mock

from pyOutlook.services.folder import FolderService
from pyOutlook.core.folder import Folder
from pyOutlook.internal.errors import AuthError, RequestError, APIError
from pyOutlook.utils.constants import BASE_API_URL


class FolderServiceTestCase(unittest.TestCase):
    """Test cases for the FolderService class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_account = Mock()
        self.mock_account._headers = {'Authorization': 'Bearer test_token'}
        self.mock_account.access_token = 'test_token'
        self.service = FolderService(self.mock_account)

    def test_init__sets_account(self):
        """Test that __init__ correctly sets the account attribute."""
        account = Mock()
        service = FolderService(account)
        self.assertEqual(service.account, account)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_all__successful_response(self, mock_check_response, mock_get):
        """Test all() returns list of folders when response is successful."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            'value': [
                {
                    'id': 'folder1',
                    'displayName': 'Inbox',
                    'parentFolderId': 'parent1',
                    'childFolderCount': 2,
                    'unreadItemCount': 5,
                    'totalItemCount': 10
                },
                {
                    'id': 'folder2',
                    'displayName': 'Sent Items',
                    'parentFolderId': 'parent1',
                    'childFolderCount': 0,
                    'unreadItemCount': 0,
                    'totalItemCount': 25
                }
            ]
        }
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        result = self.service.all()

        # Assert
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], Folder)
        self.assertIsInstance(result[1], Folder)
        self.assertEqual(result[0].id, 'folder1')
        self.assertEqual(result[0].name, 'Inbox')
        self.assertEqual(result[0].parent_id, 'parent1')
        self.assertEqual(result[0].child_folder_count, 2)
        self.assertEqual(result[0].unread_count, 5)
        self.assertEqual(result[0].total_items, 10)
        self.assertEqual(result[1].id, 'folder2')
        self.assertEqual(result[1].name, 'Sent Items')

        # Verify API call
        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/mailFolders/',
            headers=self.mock_account._headers,
            timeout=10
        )
        mock_check_response.assert_called_once_with(mock_response)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_all__check_response_returns_false(self, mock_check_response, mock_get):
        """Test all() returns empty list when check_response returns False."""
        # Arrange
        mock_response = Mock()
        mock_get.return_value = mock_response
        mock_check_response.return_value = False

        # Act
        result = self.service.all()

        # Assert
        self.assertEqual(result, [])
        mock_get.assert_called_once()
        mock_check_response.assert_called_once_with(mock_response)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_all__empty_folder_list(self, mock_check_response, mock_get):
        """Test all() returns empty list when API returns no folders."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {'value': []}
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        result = self.service.all()

        # Assert
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_get__successful_response(self, mock_check_response, mock_get):
        """Test get() returns a single folder when successful."""
        # Arrange
        folder_id = 'test_folder_id'
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': folder_id,
            'displayName': 'Test Folder',
            'parentFolderId': 'parent123',
            'childFolderCount': 3,
            'unreadItemCount': 7,
            'totalItemCount': 15
        }
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        result = self.service.get(folder_id)

        # Assert
        self.assertIsInstance(result, Folder)
        self.assertEqual(result.id, folder_id)
        self.assertEqual(result.name, 'Test Folder')
        self.assertEqual(result.parent_id, 'parent123')
        self.assertEqual(result.child_folder_count, 3)
        self.assertEqual(result.unread_count, 7)
        self.assertEqual(result.total_items, 15)
        self.assertEqual(result.account, self.mock_account)

        # Verify API call
        mock_get.assert_called_once_with(
            f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}',
            headers=self.mock_account._headers,
            timeout=10
        )
        mock_check_response.assert_called_once_with(mock_response)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_get__auth_error_raised(self, mock_check_response, mock_get):
        """Test get() raises AuthError when check_response raises it."""
        # Arrange
        folder_id = 'test_folder_id'
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        mock_check_response.side_effect = AuthError('Access token expired')

        # Act & Assert
        with self.assertRaises(AuthError):
            self.service.get(folder_id)

        mock_get.assert_called_once()
        mock_check_response.assert_called_once_with(mock_response)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_get__request_error_raised(self, mock_check_response, mock_get):
        """Test get() raises RequestError when check_response raises it."""
        # Arrange
        folder_id = 'test_folder_id'
        mock_response = Mock()
        mock_response.status_code = 400
        mock_get.return_value = mock_response
        mock_check_response.side_effect = RequestError('Bad request')

        # Act & Assert
        with self.assertRaises(RequestError):
            self.service.get(folder_id)

        mock_get.assert_called_once()

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_get__api_error_raised(self, mock_check_response, mock_get):
        """Test get() raises APIError when check_response raises it."""
        # Arrange
        folder_id = 'test_folder_id'
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        mock_check_response.side_effect = APIError('Server error')

        # Act & Assert
        with self.assertRaises(APIError):
            self.service.get(folder_id)

        mock_get.assert_called_once()

    def test_json_to_folder__creates_folder_with_all_attributes(self):
        """Test _json_to_folder() creates Folder with all attributes."""
        # Arrange
        json_data = {
            'id': 'abc123',
            'displayName': 'My Folder',
            'parentFolderId': 'parent456',
            'childFolderCount': 4,
            'unreadItemCount': 12,
            'totalItemCount': 50
        }

        # Act
        result = self.service._json_to_folder(json_data)

        # Assert
        self.assertIsInstance(result, Folder)
        self.assertEqual(result.id, 'abc123')
        self.assertEqual(result.name, 'My Folder')
        self.assertEqual(result.parent_id, 'parent456')
        self.assertEqual(result.child_folder_count, 4)
        self.assertEqual(result.unread_count, 12)
        self.assertEqual(result.total_items, 50)
        self.assertEqual(result.account, self.mock_account)

    def test_json_to_folder__with_zero_counts(self):
        """Test _json_to_folder() handles zero values correctly."""
        # Arrange
        json_data = {
            'id': 'empty_folder',
            'displayName': 'Empty',
            'parentFolderId': 'parent',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }

        # Act
        result = self.service._json_to_folder(json_data)

        # Assert
        self.assertEqual(result.child_folder_count, 0)
        self.assertEqual(result.unread_count, 0)
        self.assertEqual(result.total_items, 0)

    def test_json_to_folder__with_none_parent_id(self):
        """Test _json_to_folder() handles None parent_id (root folder)."""
        # Arrange
        json_data = {
            'id': 'root_folder',
            'displayName': 'Root',
            'parentFolderId': None,
            'childFolderCount': 5,
            'unreadItemCount': 1,
            'totalItemCount': 100
        }

        # Act
        result = self.service._json_to_folder(json_data)

        # Assert
        self.assertIsNone(result.parent_id)
        self.assertEqual(result.id, 'root_folder')

    def test_json_to_folders__creates_list_of_folders(self):
        """Test _json_to_folders() creates list of Folder objects."""
        # Arrange
        json_data = {
            'value': [
                {
                    'id': 'folder1',
                    'displayName': 'Folder One',
                    'parentFolderId': 'parent1',
                    'childFolderCount': 1,
                    'unreadItemCount': 2,
                    'totalItemCount': 3
                },
                {
                    'id': 'folder2',
                    'displayName': 'Folder Two',
                    'parentFolderId': 'parent2',
                    'childFolderCount': 4,
                    'unreadItemCount': 5,
                    'totalItemCount': 6
                },
                {
                    'id': 'folder3',
                    'displayName': 'Folder Three',
                    'parentFolderId': 'parent3',
                    'childFolderCount': 7,
                    'unreadItemCount': 8,
                    'totalItemCount': 9
                }
            ]
        }

        # Act
        result = self.service._json_to_folders(json_data)

        # Assert
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], Folder)
        self.assertIsInstance(result[1], Folder)
        self.assertIsInstance(result[2], Folder)

        # Verify first folder
        self.assertEqual(result[0].id, 'folder1')
        self.assertEqual(result[0].name, 'Folder One')

        # Verify second folder
        self.assertEqual(result[1].id, 'folder2')
        self.assertEqual(result[1].name, 'Folder Two')

        # Verify third folder
        self.assertEqual(result[2].id, 'folder3')
        self.assertEqual(result[2].name, 'Folder Three')

    def test_json_to_folders__empty_value_array(self):
        """Test _json_to_folders() handles empty value array."""
        # Arrange
        json_data = {'value': []}

        # Act
        result = self.service._json_to_folders(json_data)

        # Assert
        self.assertEqual(result, [])
        self.assertIsInstance(result, list)

    def test_json_to_folders__single_folder(self):
        """Test _json_to_folders() handles single folder in value array."""
        # Arrange
        json_data = {
            'value': [
                {
                    'id': 'single',
                    'displayName': 'Single Folder',
                    'parentFolderId': 'parent',
                    'childFolderCount': 0,
                    'unreadItemCount': 1,
                    'totalItemCount': 1
                }
            ]
        }

        # Act
        result = self.service._json_to_folders(json_data)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Folder)
        self.assertEqual(result[0].id, 'single')
        self.assertEqual(result[0].name, 'Single Folder')

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_all__verifies_account_headers_used(self, mock_check_response, mock_get):
        """Test all() uses the account's headers for authentication."""
        # Arrange
        custom_headers = {'Authorization': 'Bearer custom_token', 'Custom': 'Header'}
        self.mock_account._headers = custom_headers
        mock_response = Mock()
        mock_response.json.return_value = {'value': []}
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        self.service.all()

        # Assert
        mock_get.assert_called_once_with(
            'https://graph.microsoft.com/v1.0/me/mailFolders/',
            headers=custom_headers,
            timeout=10
        )

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_get__verifies_account_headers_used(self, mock_check_response, mock_get):
        """Test get() uses the account's headers for authentication."""
        # Arrange
        custom_headers = {'Authorization': 'Bearer custom_token', 'Custom': 'Header'}
        self.mock_account._headers = custom_headers
        folder_id = 'test_id'
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': folder_id,
            'displayName': 'Test',
            'parentFolderId': 'p',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        self.service.get(folder_id)

        # Assert
        mock_get.assert_called_once_with(
            f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}',
            headers=custom_headers,
            timeout=10
        )

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_get__special_characters_in_folder_id(self, mock_check_response, mock_get):
        """Test get() handles folder IDs with special characters."""
        # Arrange
        folder_id = 'AAMkAGI2TnVkLTU3My00Zjc0LWJlY2UtZGNhYmQzNDI1M2RlAC4AAAAAAADOyI9eRrXXS43ztd8PcdkVAQBfPom5TGdBTqP8OYSOcC8vAAAAAAEMAAA='
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': folder_id,
            'displayName': 'Special',
            'parentFolderId': 'parent',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        result = self.service.get(folder_id)

        # Assert
        self.assertEqual(result.id, folder_id)
        mock_get.assert_called_once_with(
            f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}',
            headers=self.mock_account._headers,
            timeout=10
        )

    def test_json_to_folder__preserves_account_reference(self):
        """Test _json_to_folder() preserves the account reference in created folder."""
        # Arrange
        json_data = {
            'id': 'test',
            'displayName': 'Test',
            'parentFolderId': 'parent',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }

        # Act
        result = self.service._json_to_folder(json_data)

        # Assert
        self.assertIs(result.account, self.mock_account)

    def test_json_to_folders__all_folders_have_account_reference(self):
        """Test _json_to_folders() ensures all folders have account reference."""
        # Arrange
        json_data = {
            'value': [
                {
                    'id': 'f1',
                    'displayName': 'F1',
                    'parentFolderId': 'p',
                    'childFolderCount': 0,
                    'unreadItemCount': 0,
                    'totalItemCount': 0
                },
                {
                    'id': 'f2',
                    'displayName': 'F2',
                    'parentFolderId': 'p',
                    'childFolderCount': 0,
                    'unreadItemCount': 0,
                    'totalItemCount': 0
                }
            ]
        }

        # Act
        result = self.service._json_to_folders(json_data)

        # Assert
        for folder in result:
            self.assertIs(folder.account, self.mock_account)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_all__timeout_parameter_set(self, mock_check_response, mock_get):
        """Test all() sets timeout parameter to 10 seconds."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {'value': []}
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        self.service.all()

        # Assert
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['timeout'], 10)

    @patch('pyOutlook.services.folder.requests.get')
    @patch('pyOutlook.services.folder.check_response')
    def test_get__timeout_parameter_set(self, mock_check_response, mock_get):
        """Test get() sets timeout parameter to 10 seconds."""
        # Arrange
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'test',
            'displayName': 'Test',
            'parentFolderId': 'p',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }
        mock_get.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        self.service.get('test')

        # Assert
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['timeout'], 10)

    @patch('pyOutlook.services.folder.requests.post')
    @patch('pyOutlook.services.folder.check_response')
    def test_create__successful_response(self, mock_check_response, mock_post):
        """Test create() returns a Folder when successful."""
        # Arrange
        folder_name = 'My New Folder'
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'new_folder_id',
            'displayName': folder_name,
            'parentFolderId': 'parent123',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }
        mock_post.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        result = self.service.create(folder_name)

        # Assert
        self.assertIsInstance(result, Folder)
        self.assertEqual(result.id, 'new_folder_id')
        self.assertEqual(result.name, folder_name)
        self.assertEqual(result.parent_id, 'parent123')
        self.assertEqual(result.child_folder_count, 0)
        self.assertEqual(result.unread_count, 0)
        self.assertEqual(result.total_items, 0)
        self.assertEqual(result.account, self.mock_account)

        # Verify API call
        mock_post.assert_called_once_with(
            f'{BASE_API_URL}/me/mailFolders',
            headers=self.mock_account._headers,
            data=json.dumps({'displayName': folder_name}),
            timeout=10
        )
        mock_check_response.assert_called_once_with(mock_response)

    @patch('pyOutlook.services.folder.requests.post')
    @patch('pyOutlook.services.folder.check_response')
    def test_create__auth_error_raised(self, mock_check_response, mock_post):
        """Test create() raises AuthError when check_response raises it."""
        # Arrange
        folder_name = 'My Folder'
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response
        mock_check_response.side_effect = AuthError('Access token expired')

        # Act & Assert
        with self.assertRaises(AuthError):
            self.service.create(folder_name)

        mock_post.assert_called_once()
        mock_check_response.assert_called_once_with(mock_response)

    @patch('pyOutlook.services.folder.requests.post')
    @patch('pyOutlook.services.folder.check_response')
    def test_create__request_error_raised(self, mock_check_response, mock_post):
        """Test create() raises RequestError when check_response raises it."""
        # Arrange
        folder_name = 'My Folder'
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        mock_check_response.side_effect = RequestError('Bad request')

        # Act & Assert
        with self.assertRaises(RequestError):
            self.service.create(folder_name)

        mock_post.assert_called_once()

    @patch('pyOutlook.services.folder.requests.post')
    @patch('pyOutlook.services.folder.check_response')
    def test_create__api_error_raised(self, mock_check_response, mock_post):
        """Test create() raises APIError when check_response raises it."""
        # Arrange
        folder_name = 'My Folder'
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        mock_check_response.side_effect = APIError('Server error')

        # Act & Assert
        with self.assertRaises(APIError):
            self.service.create(folder_name)

        mock_post.assert_called_once()

    @patch('pyOutlook.services.folder.requests.post')
    @patch('pyOutlook.services.folder.check_response')
    def test_create__verifies_account_headers_used(self, mock_check_response, mock_post):
        """Test create() uses the account's headers for authentication."""
        # Arrange
        custom_headers = {'Authorization': 'Bearer custom_token', 'Custom': 'Header'}
        self.mock_account._headers = custom_headers
        folder_name = 'My Folder'
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'test',
            'displayName': folder_name,
            'parentFolderId': 'p',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }
        mock_post.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        self.service.create(folder_name)

        # Assert
        mock_post.assert_called_once_with(
            f'{BASE_API_URL}/me/mailFolders',
            headers=custom_headers,
            data=json.dumps({'displayName': folder_name}),
            timeout=10
        )

    @patch('pyOutlook.services.folder.requests.post')
    @patch('pyOutlook.services.folder.check_response')
    def test_create__timeout_parameter_set(self, mock_check_response, mock_post):
        """Test create() sets timeout parameter to 10 seconds."""
        # Arrange
        folder_name = 'My Folder'
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'test',
            'displayName': folder_name,
            'parentFolderId': 'p',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }
        mock_post.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        self.service.create(folder_name)

        # Assert
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['timeout'], 10)

    @patch('pyOutlook.services.folder.requests.post')
    @patch('pyOutlook.services.folder.check_response')
    def test_create__payload_correct_format(self, mock_check_response, mock_post):
        """Test create() sends payload in correct JSON format."""
        # Arrange
        folder_name = 'Test Folder Name'
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 'test',
            'displayName': folder_name,
            'parentFolderId': 'p',
            'childFolderCount': 0,
            'unreadItemCount': 0,
            'totalItemCount': 0
        }
        mock_post.return_value = mock_response
        mock_check_response.return_value = True

        # Act
        self.service.create(folder_name)

        # Assert
        import json
        call_args = mock_post.call_args
        payload = call_args[1]['data']
        self.assertEqual(payload, json.dumps({'displayName': folder_name}))


if __name__ == '__main__':
    unittest.main()
