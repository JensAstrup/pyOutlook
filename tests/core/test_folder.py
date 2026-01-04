import unittest
try:
    from unittest.mock import patch, Mock, MagicMock
except ImportError:
    from mock import Mock, MagicMock, patch

from pyOutlook.core.folder import Folder
from pyOutlook.internal.errors import AuthError, RequestError, APIError


class FolderTestCase(unittest.TestCase):
    """Test suite for the Folder class"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.mock_account = Mock()
        self.mock_account.access_token = 'test_access_token'

        self.test_folder = Folder(
            account=self.mock_account,
            folder_id='test_folder_id',
            folder_name='Test Folder',
            parent_id='parent_folder_id',
            child_folder_count=5,
            unread_count=10,
            total_items=25
        )

    def test_init__all_attributes_set_correctly(self):
        """Test that __init__ sets all attributes correctly"""
        folder = Folder(
            account=self.mock_account,
            folder_id='folder123',
            folder_name='My Folder',
            parent_id='parent123',
            child_folder_count=3,
            unread_count=7,
            total_items=15
        )

        self.assertEqual(folder.account, self.mock_account)
        self.assertEqual(folder.id, 'folder123')
        self.assertEqual(folder.name, 'My Folder')
        self.assertEqual(folder.parent_id, 'parent123')
        self.assertEqual(folder.child_folder_count, 3)
        self.assertEqual(folder.unread_count, 7)
        self.assertEqual(folder.total_items, 15)

    def test_str__returns_folder_name(self):
        """Test that __str__ returns the folder name"""
        result = str(self.test_folder)
        self.assertEqual(result, 'Test Folder')

    def test_repr__returns_folder_name(self):
        """Test that __repr__ returns the folder name"""
        result = repr(self.test_folder)
        self.assertEqual(result, 'Test Folder')

    def test_headers__returns_correct_authorization_header(self):
        """Test that headers property returns correct authorization and content type"""
        expected_headers = {
            "Authorization": "Bearer test_access_token",
            "Content-Type": "application/json"
        }

        self.assertEqual(self.test_folder.headers, expected_headers)

    def test_headers__with_different_token(self):
        """Test that headers property uses the current access token"""
        self.mock_account.access_token = 'different_token'

        expected_headers = {
            "Authorization": "Bearer different_token",
            "Content-Type": "application/json"
        }

        self.assertEqual(self.test_folder.headers, expected_headers)

    @patch('pyOutlook.services.folder.FolderService')
    def test_json_to_folder__delegates_to_folder_service(self, mock_folder_service):
        """Test that _json_to_folder delegates to FolderService"""
        mock_json = {'Id': 'test_id', 'DisplayName': 'Test'}
        mock_folder_service._json_to_folder.return_value = self.test_folder

        result = Folder._json_to_folder(self.mock_account, mock_json)

        mock_folder_service._json_to_folder.assert_called_once_with(self.mock_account, mock_json)
        self.assertEqual(result, self.test_folder)

    @patch('pyOutlook.services.folder.FolderService')
    def test_json_to_folders__delegates_to_folder_service(self, mock_folder_service):
        """Test that _json_to_folders delegates to FolderService"""
        mock_json = {'value': [{'Id': 'test_id', 'DisplayName': 'Test'}]}
        mock_folders = [self.test_folder]
        mock_folder_service._json_to_folders.return_value = mock_folders

        result = Folder._json_to_folders(self.mock_account, mock_json)

        mock_folder_service._json_to_folders.assert_called_once_with(self.mock_account, mock_json)
        self.assertEqual(result, mock_folders)

    @patch('pyOutlook.core.folder.requests.patch')
    @patch('pyOutlook.core.folder.check_response')
    def test_rename__successful_rename(self, mock_check_response, mock_patch):
        """Test successful folder rename"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Id': 'test_folder_id',
            'DisplayName': 'Renamed Folder',
            'ParentFolderId': 'parent_folder_id',
            'ChildFolderCount': 5,
            'UnreadItemCount': 10,
            'TotalItemCount': 25
        }
        mock_patch.return_value = mock_response

        with patch.object(Folder, '_json_to_folder') as mock_json_to_folder:
            renamed_folder = Mock()
            renamed_folder.name = 'Renamed Folder'
            mock_json_to_folder.return_value = renamed_folder

            result = self.test_folder.rename('Renamed Folder')

            # Verify correct endpoint and payload
            mock_patch.assert_called_once()
            call_args = mock_patch.call_args
            self.assertIn('test_folder_id', call_args[0][0])
            self.assertIn('Renamed Folder', call_args[1]['data'])

            # Verify headers
            self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_access_token')

            # Verify result
            self.assertEqual(result, renamed_folder)

    @patch('pyOutlook.core.folder.requests.patch')
    @patch('pyOutlook.core.folder.check_response')
    def test_rename__check_response_fails(self, mock_check_response, mock_patch):
        """Test rename when check_response fails"""
        mock_check_response.return_value = False
        mock_response = Mock()
        mock_response.status_code = 200
        mock_patch.return_value = mock_response

        result = self.test_folder.rename('New Name')

        # Should return None when check_response returns False
        self.assertIsNone(result)

    @patch('pyOutlook.core.folder.requests.patch')
    @patch('pyOutlook.core.folder.check_response')
    def test_rename__auth_error_raised(self, mock_check_response, mock_patch):
        """Test rename raises AuthError on 401"""
        mock_check_response.side_effect = AuthError('Invalid token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_patch.return_value = mock_response

        with self.assertRaises(AuthError):
            self.test_folder.rename('New Name')

    @patch('pyOutlook.core.folder.requests.get')
    @patch('pyOutlook.core.folder.check_response')
    def test_get_subfolders__successful_retrieval(self, mock_check_response, mock_get):
        """Test successful subfolder retrieval"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {
                    'Id': 'subfolder1',
                    'DisplayName': 'Subfolder 1',
                    'ParentFolderId': 'test_folder_id',
                    'ChildFolderCount': 0,
                    'UnreadItemCount': 2,
                    'TotalItemCount': 5
                }
            ]
        }
        mock_get.return_value = mock_response

        with patch.object(Folder, '_json_to_folders') as mock_json_to_folders:
            mock_subfolders = [Mock()]
            mock_json_to_folders.return_value = mock_subfolders

            result = self.test_folder.get_subfolders()

            # Verify correct endpoint
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            self.assertIn('test_folder_id', call_args[0][0])
            self.assertIn('childfolders', call_args[0][0])

            # Verify headers
            self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_access_token')

            # Verify result
            self.assertEqual(result, mock_subfolders)

    @patch('pyOutlook.core.folder.requests.get')
    @patch('pyOutlook.core.folder.check_response')
    def test_get_subfolders__check_response_fails(self, mock_check_response, mock_get):
        """Test get_subfolders when check_response fails"""
        mock_check_response.return_value = False
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = self.test_folder.get_subfolders()

        # Should return None when check_response returns False
        self.assertIsNone(result)

    @patch('pyOutlook.core.folder.requests.get')
    @patch('pyOutlook.core.folder.check_response')
    def test_get_subfolders__auth_error_raised(self, mock_check_response, mock_get):
        """Test get_subfolders raises AuthError on 401"""
        mock_check_response.side_effect = AuthError('Invalid token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(AuthError):
            self.test_folder.get_subfolders()

    @patch('pyOutlook.core.folder.requests.delete')
    @patch('pyOutlook.core.folder.check_response')
    def test_delete__successful_deletion(self, mock_check_response, mock_delete):
        """Test successful folder deletion"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        # Should not raise any exception
        self.test_folder.delete()

        # Verify correct endpoint
        mock_delete.assert_called_once()
        call_args = mock_delete.call_args
        self.assertIn('test_folder_id', call_args[0][0])

        # Verify headers
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_access_token')

    @patch('pyOutlook.core.folder.requests.delete')
    @patch('pyOutlook.core.folder.check_response')
    def test_delete__auth_error_raised(self, mock_check_response, mock_delete):
        """Test delete raises AuthError on 401"""
        mock_check_response.side_effect = AuthError('Invalid token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_delete.return_value = mock_response

        with self.assertRaises(AuthError):
            self.test_folder.delete()

    @patch('pyOutlook.core.folder.requests.delete')
    @patch('pyOutlook.core.folder.check_response')
    def test_delete__request_error_raised(self, mock_check_response, mock_delete):
        """Test delete raises RequestError on 400"""
        mock_check_response.side_effect = RequestError('Bad request')
        mock_response = Mock()
        mock_response.status_code = 400
        mock_delete.return_value = mock_response

        with self.assertRaises(RequestError):
            self.test_folder.delete()

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_move_into__successful_move(self, mock_check_response, mock_post):
        """Test successful folder move"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Id': 'test_folder_id',
            'DisplayName': 'Test Folder',
            'ParentFolderId': 'destination_folder_id',
            'ChildFolderCount': 5,
            'UnreadItemCount': 10,
            'TotalItemCount': 25
        }
        mock_post.return_value = mock_response

        destination_folder = Folder(
            account=self.mock_account,
            folder_id='destination_folder_id',
            folder_name='Destination',
            parent_id=None,
            child_folder_count=1,
            unread_count=0,
            total_items=0
        )

        with patch.object(Folder, '_json_to_folder') as mock_json_to_folder:
            moved_folder = Mock()
            moved_folder.parent_id = 'destination_folder_id'
            mock_json_to_folder.return_value = moved_folder

            result = self.test_folder.move_into(destination_folder)

            # Verify correct endpoint and payload
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn('test_folder_id', call_args[0][0])
            self.assertIn('move', call_args[0][0])
            self.assertIn('destination_folder_id', call_args[1]['data'])

            # Verify headers
            self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_access_token')

            # Verify result
            self.assertEqual(result, moved_folder)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_move_into__check_response_fails(self, mock_check_response, mock_post):
        """Test move_into when check_response fails"""
        mock_check_response.return_value = False
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        destination_folder = Folder(
            account=self.mock_account,
            folder_id='destination_folder_id',
            folder_name='Destination',
            parent_id=None,
            child_folder_count=1,
            unread_count=0,
            total_items=0
        )

        result = self.test_folder.move_into(destination_folder)

        # Should return None when check_response returns False
        self.assertIsNone(result)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_move_into__auth_error_raised(self, mock_check_response, mock_post):
        """Test move_into raises AuthError on 401"""
        mock_check_response.side_effect = AuthError('Invalid token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        destination_folder = Folder(
            account=self.mock_account,
            folder_id='destination_folder_id',
            folder_name='Destination',
            parent_id=None,
            child_folder_count=1,
            unread_count=0,
            total_items=0
        )

        with self.assertRaises(AuthError):
            self.test_folder.move_into(destination_folder)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_copy_into__successful_copy(self, mock_check_response, mock_post):
        """Test successful folder copy"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Id': 'new_folder_id',
            'DisplayName': 'Test Folder',
            'ParentFolderId': 'destination_folder_id',
            'ChildFolderCount': 5,
            'UnreadItemCount': 10,
            'TotalItemCount': 25
        }
        mock_post.return_value = mock_response

        destination_folder = Folder(
            account=self.mock_account,
            folder_id='destination_folder_id',
            folder_name='Destination',
            parent_id=None,
            child_folder_count=1,
            unread_count=0,
            total_items=0
        )

        with patch.object(Folder, '_json_to_folder') as mock_json_to_folder:
            copied_folder = Mock()
            copied_folder.id = 'new_folder_id'
            mock_json_to_folder.return_value = copied_folder

            result = self.test_folder.copy_into(destination_folder)

            # Verify correct endpoint and payload
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn('test_folder_id', call_args[0][0])
            self.assertIn('copy', call_args[0][0])
            self.assertIn('destination_folder_id', call_args[1]['data'])

            # Verify headers
            self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_access_token')

            # Verify result
            self.assertEqual(result, copied_folder)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_copy_into__check_response_fails(self, mock_check_response, mock_post):
        """Test copy_into when check_response fails"""
        mock_check_response.return_value = False
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        destination_folder = Folder(
            account=self.mock_account,
            folder_id='destination_folder_id',
            folder_name='Destination',
            parent_id=None,
            child_folder_count=1,
            unread_count=0,
            total_items=0
        )

        result = self.test_folder.copy_into(destination_folder)

        # Should return None when check_response returns False
        self.assertIsNone(result)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_copy_into__auth_error_raised(self, mock_check_response, mock_post):
        """Test copy_into raises AuthError on 401"""
        mock_check_response.side_effect = AuthError('Invalid token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        destination_folder = Folder(
            account=self.mock_account,
            folder_id='destination_folder_id',
            folder_name='Destination',
            parent_id=None,
            child_folder_count=1,
            unread_count=0,
            total_items=0
        )

        with self.assertRaises(AuthError):
            self.test_folder.copy_into(destination_folder)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_create_child_folder__successful_creation(self, mock_check_response, mock_post):
        """Test successful child folder creation"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            'Id': 'new_child_folder_id',
            'DisplayName': 'New Child',
            'ParentFolderId': 'test_folder_id',
            'ChildFolderCount': 0,
            'UnreadItemCount': 0,
            'TotalItemCount': 0
        }
        mock_post.return_value = mock_response

        with patch.object(Folder, '_json_to_folder') as mock_json_to_folder:
            child_folder = Mock()
            child_folder.name = 'New Child'
            child_folder.parent_id = 'test_folder_id'
            mock_json_to_folder.return_value = child_folder

            result = self.test_folder.create_child_folder('New Child')

            # Verify correct endpoint and payload
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertIn('test_folder_id', call_args[0][0])
            self.assertIn('childfolders', call_args[0][0])
            self.assertIn('New Child', call_args[1]['data'])

            # Verify headers
            self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_access_token')

            # Verify result
            self.assertEqual(result, child_folder)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_create_child_folder__check_response_fails(self, mock_check_response, mock_post):
        """Test create_child_folder when check_response fails"""
        mock_check_response.return_value = False
        mock_response = Mock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = self.test_folder.create_child_folder('New Child')

        # Should return None when check_response returns False
        self.assertIsNone(result)

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_create_child_folder__auth_error_raised(self, mock_check_response, mock_post):
        """Test create_child_folder raises AuthError on 401"""
        mock_check_response.side_effect = AuthError('Invalid token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_post.return_value = mock_response

        with self.assertRaises(AuthError):
            self.test_folder.create_child_folder('New Child')

    @patch('pyOutlook.core.folder.requests.post')
    @patch('pyOutlook.core.folder.check_response')
    def test_create_child_folder__request_error_raised(self, mock_check_response, mock_post):
        """Test create_child_folder raises RequestError on 400"""
        mock_check_response.side_effect = RequestError('Invalid folder name')
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response

        with self.assertRaises(RequestError):
            self.test_folder.create_child_folder('Invalid@Name')

    @patch('pyOutlook.services.message.MessageService')
    @patch('pyOutlook.core.folder.requests.get')
    @patch('pyOutlook.core.folder.check_response')
    def test_messages__successful_retrieval(self, mock_check_response, mock_get, mock_message_service):
        """Test successful message retrieval from folder"""
        mock_check_response.return_value = True
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {
                    'Id': 'message1',
                    'Subject': 'Test Message 1'
                },
                {
                    'Id': 'message2',
                    'Subject': 'Test Message 2'
                }
            ]
        }
        mock_get.return_value = mock_response

        mock_messages = [Mock(), Mock()]
        mock_message_service._json_to_messages.return_value = mock_messages

        result = self.test_folder.messages()

        # Verify correct endpoint
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('test_folder_id', call_args[0][0])
        self.assertIn('messages', call_args[0][0])

        # Verify headers
        self.assertEqual(call_args[1]['headers']['Authorization'], 'Bearer test_access_token')

        # Verify MessageService was called correctly
        mock_message_service._json_to_messages.assert_called_once_with(
            self.mock_account,
            mock_response.json.return_value
        )

        # Verify result
        self.assertEqual(result, mock_messages)

    @patch('pyOutlook.services.message.MessageService')
    @patch('pyOutlook.core.folder.requests.get')
    @patch('pyOutlook.core.folder.check_response')
    def test_messages__auth_error_raised(self, mock_check_response, mock_get, mock_message_service):
        """Test messages raises AuthError on 401"""
        mock_check_response.side_effect = AuthError('Invalid token')
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        with self.assertRaises(AuthError):
            self.test_folder.messages()

    @patch('pyOutlook.services.message.MessageService')
    @patch('pyOutlook.core.folder.requests.get')
    @patch('pyOutlook.core.folder.check_response')
    def test_messages__api_error_raised(self, mock_check_response, mock_get, mock_message_service):
        """Test messages raises APIError on unknown error"""
        mock_check_response.side_effect = APIError('Unknown error')
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        with self.assertRaises(APIError):
            self.test_folder.messages()

    def test_rename__special_characters_in_name(self):
        """Test rename with special characters in folder name"""
        with patch('pyOutlook.core.folder.requests.patch') as mock_patch, \
             patch('pyOutlook.core.folder.check_response') as mock_check_response:
            mock_check_response.return_value = True
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'Id': 'test_folder_id',
                'DisplayName': 'Folder "with" quotes',
                'ParentFolderId': 'parent_folder_id',
                'ChildFolderCount': 0,
                'UnreadItemCount': 0,
                'TotalItemCount': 0
            }
            mock_patch.return_value = mock_response

            with patch.object(Folder, '_json_to_folder') as mock_json_to_folder:
                renamed_folder = Mock()
                mock_json_to_folder.return_value = renamed_folder

                self.test_folder.rename('Folder "with" quotes')

                # Verify payload contains the special characters
                call_args = mock_patch.call_args
                self.assertIn('Folder "with" quotes', call_args[1]['data'])

    def test_create_child_folder__empty_folder_name(self):
        """Test create_child_folder with empty folder name"""
        with patch('pyOutlook.core.folder.requests.post') as mock_post, \
             patch('pyOutlook.core.folder.check_response') as mock_check_response:
            mock_check_response.return_value = True
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                'Id': 'new_folder_id',
                'DisplayName': '',
                'ParentFolderId': 'test_folder_id',
                'ChildFolderCount': 0,
                'UnreadItemCount': 0,
                'TotalItemCount': 0
            }
            mock_post.return_value = mock_response

            with patch.object(Folder, '_json_to_folder') as mock_json_to_folder:
                child_folder = Mock()
                mock_json_to_folder.return_value = child_folder

                result = self.test_folder.create_child_folder('')

                # Verify the empty string is passed in payload
                call_args = mock_post.call_args
                self.assertIn('""', call_args[1]['data'])

    def test_headers__property_access_multiple_times(self):
        """Test that headers property can be accessed multiple times"""
        headers1 = self.test_folder.headers
        headers2 = self.test_folder.headers

        # Should return the same structure each time
        self.assertEqual(headers1, headers2)
        self.assertEqual(headers1['Authorization'], 'Bearer test_access_token')

    def test_move_into__same_destination_as_current_parent(self):
        """Test moving folder into its current parent folder"""
        with patch('pyOutlook.core.folder.requests.post') as mock_post, \
             patch('pyOutlook.core.folder.check_response') as mock_check_response:
            mock_check_response.return_value = True
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'Id': 'test_folder_id',
                'DisplayName': 'Test Folder',
                'ParentFolderId': 'parent_folder_id',
                'ChildFolderCount': 5,
                'UnreadItemCount': 10,
                'TotalItemCount': 25
            }
            mock_post.return_value = mock_response

            # Create destination folder with same ID as current parent
            same_parent_folder = Folder(
                account=self.mock_account,
                folder_id='parent_folder_id',
                folder_name='Parent',
                parent_id=None,
                child_folder_count=1,
                unread_count=0,
                total_items=0
            )

            with patch.object(Folder, '_json_to_folder') as mock_json_to_folder:
                moved_folder = Mock()
                mock_json_to_folder.return_value = moved_folder

                result = self.test_folder.move_into(same_parent_folder)

                # Verify the operation still completes
                self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
