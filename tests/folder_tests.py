from unittest import TestCase
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import Mock, patch
from pyOutlook import *


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

    def test_api_representation(self):
        """ Test that a Folder is correctly converted from JSON """
        mock = Mock()
        mock.status_code = 200
        json_folder = {
            "@odata.context": "https://outlook.office.com/api/v2.0/$metadata#Me/MailFolders/$entity",
            "@odata.id": "http-1d94-4d0c-9AEMAAA=')",
            "Id": "AAMkAGI2AAEMAAA=",
            "DisplayName": "Inbox",
            "ParentFolderId": "AAMkAGI2AAEIAAA=",
            "ChildFolderCount": 0,
            "UnreadItemCount": 6,
            "TotalItemCount": 7
        }
        mock.json.return_value = json_folder

        self.mock_get.return_value = mock

        folder = self.account.get_folder_by_id('AAMkAGI2AAEMAAA=')

        self.assertEqual(folder.name, json_folder['DisplayName'])
        self.assertEqual(folder.unread_count, json_folder['UnreadItemCount'])
        self.assertEqual(folder.total_items, json_folder['TotalItemCount'])

    def test_rename_folder(self):
        """ A new folder with the new name should be returned """
        mock = Mock()
        mock.status_code = 200
        json_folder = {
            "@odata.context": "https://outlook.office.com/api/v2.0/$metadata#Me/MailFolders/$entity",
            "@odata.id": "http-1d94-4d0c-9AEMAAA=')",
            "Id": "AAMkAGI2AAEMAAA=",
            "DisplayName": "Inbox2",
            "ParentFolderId": "AAMkAGI2AAEIAAA=",
            "ChildFolderCount": 0,
            "UnreadItemCount": 6,
            "TotalItemCount": 7
        }
        mock.json.return_value = json_folder

        self.mock_patch.return_value = mock

        folder_a = Folder(self.account, '123', 'Inbox', None, 1, 2, 3)
        folder_b = folder_a.rename('Inbox2')

        self.assertEqual(folder_b.name, 'Inbox2')

    def test_rename_folder_based_on_api_response(self):
        """ A new folder with the new name should be returned - but it should use what the API returns back, not what
        the user provides (if there's an issue with the request to the API, it won't be masked by setting the intended
        value instead of the returned one). """
        mock = Mock()
        mock.status_code = 200
        json_folder = {
            "@odata.context": "https://outlook.office.com/api/v2.0/$metadata#Me/MailFolders/$entity",
            "@odata.id": "http-1d94-4d0c-9AEMAAA=')",
            "Id": "AAMkAGI2AAEMAAA=",
            "DisplayName": "Inbox2",
            "ParentFolderId": "AAMkAGI2AAEIAAA=",
            "ChildFolderCount": 0,
            "UnreadItemCount": 6,
            "TotalItemCount": 7
        }
        mock.json.return_value = json_folder

        self.mock_patch.return_value = mock

        folder_a = Folder(self.account, '123', 'Inbox', None, 1, 2, 3)
        folder_b = folder_a.rename('InboxB')

        self.assertEqual(folder_b.name, 'Inbox2')