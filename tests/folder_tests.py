import json
import six

from unittest import TestCase
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import Mock, patch
from pyOutlook import *


class FolderTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.account = OutlookAccount('token')
        cls.folder = Folder(cls.account, 'ID', 'Test Name', 'Parent ID', 0, 0, 1)

    def test__str__(self):
        self.assertEqual(str(self.folder), 'Test Name')

    def test__repr__(self):
        self.assertEqual(repr(self.folder), 'Test Name')

    def test__eq__true(self):
        same_folder = Folder(self.account, 'ID', 'Test Name', 'Parent ID', 0, 0, 1)
        self.assertEqual(self.folder, same_folder)

    def test__eq__false(self):
        other_folder = Folder(self.account, 'Different', 'Test Name', 'Parent ID', 0, 0, 1)
        self.assertNotEqual(self.folder, other_folder)

    def test__hash__(self):
        expected = hash(self.folder.id)
        self.assertEqual(hash(self.folder), expected)

    def test_json_to_folders(self):
        folders = dict(value=[
            dict(Id='Folder1',
                 DisplayName='Folder 1',
                 ParentFolderId='Parent Folder',
                 ChildFolderCount=3,
                 UnreadItemCount=4,
                 TotalItemCount=20),
            dict(Id='Folder2',
                 DisplayName='Folder 2',
                 ParentFolderId='Parent Folder 2',
                 ChildFolderCount=0,
                 UnreadItemCount=2,
                 TotalItemCount=10),
        ])
        expected = [
            Folder(self.account, 'Folder1', 'Folder 1', 'Parent Folder', 3, 4, 20),
            Folder(self.account, 'Folder2', 'Folder 2', 'Parent Folder 2', 0, 2, 10)
        ]
        six.assertCountEqual(self, Folder._json_to_folders(self.account, folders), expected)

    @patch('pyOutlook.core.folder.requests.patch')
    def test_rename_folder(self, patch):
        """ A new folder with the new name should be returned """
        response = Mock()
        response.status_code = 200
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
        response.json.return_value = json_folder

        patch.return_value = response

        folder_a = Folder(self.account, '123', 'Inbox', None, 1, 2, 3)
        folder_b = folder_a.rename('Inbox2')

        self.assertEqual(folder_b.name, 'Inbox2')

    @patch('pyOutlook.core.folder.requests.patch')
    def test_rename_folder_based_on_api_response(self, patch):
        """ A new folder with the new name should be returned - but it should use what the API returns back, not what
        the user provides (if there's an issue with the request to the API, it won't be masked by setting the intended
        value instead of the returned one). """
        response = Mock()
        response.status_code = 200
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
        response.json.return_value = json_folder

        patch.return_value = response

        folder_a = Folder(self.account, '123', 'Inbox', None, 1, 2, 3)
        folder_b = folder_a.rename('InboxB')

        self.assertEqual(folder_b.name, 'Inbox2')

    @patch('pyOutlook.core.folder.requests.get')
    def test_get_subfolders(self, get):
        json_folders = dict(value=[
            dict(Id='Folder1',
                 DisplayName='Folder 1',
                 ParentFolderId='Parent Folder',
                 ChildFolderCount=3,
                 UnreadItemCount=4,
                 TotalItemCount=20),
            dict(Id='Folder2',
                 DisplayName='Folder 2',
                 ParentFolderId='Parent Folder 2',
                 ChildFolderCount=0,
                 UnreadItemCount=2,
                 TotalItemCount=10),
        ])
        response = Mock()
        response.status_code = 200
        response.json.return_value = json_folders

        get.return_value = response

        expected = [
            Folder(self.account, 'Folder1', 'Folder 1', 'Parent Folder', 3, 4, 20),
            Folder(self.account, 'Folder2', 'Folder 2', 'Parent Folder 2', 0, 2, 10)
        ]
        six.assertCountEqual(self, self.folder.get_subfolders(), expected)
        expected_url = 'https://outlook.office.com/api/v2.0/me/MailFolders/ID/childfolders'
        get.assert_called_once_with(expected_url, headers=self.folder.headers)

    @patch('pyOutlook.core.folder.check_response')
    @patch('pyOutlook.core.folder.requests.delete')
    def test_delete(self, delete, check_response):
        response = Mock()
        response.status_code = 200
        delete.return_value = response
        self.folder.delete()
        expected_url = 'https://outlook.office.com/api/v2.0/me/MailFolders/ID'
        delete.assert_called_once_with(expected_url, headers=self.folder.headers)
        check_response.assert_called_once_with(response)

    @patch.object(Folder, '_json_to_folder')
    @patch('pyOutlook.core.folder.check_response')
    @patch('pyOutlook.core.folder.requests.post')
    def test_move_into(self, post, check_response, json_to_folder):
        new_parent_folder = Folder(self.account, 'Folder1', 'Folder 1', 'Parent Folder', 3, 4, 20)
        response = Mock()
        response.status_code = 200
        response.json.return_value = dict(Id='Folder1',
                                          DisplayName='Folder 1',
                                          ParentFolderId='Parent Folder',
                                          ChildFolderCount=3,
                                          UnreadItemCount=4,
                                          TotalItemCount=20)
        post.return_value = response
        json_to_folder.return_value = self.folder

        new_folder = self.folder.move_into(new_parent_folder)
        expected_url = 'https://outlook.office.com/api/v2.0/me/MailFolders/ID/move'
        expected_payload = dict(DestinationId='Folder1')
        post.assert_called_once_with(expected_url, headers=self.folder.headers, data=json.dumps(expected_payload))
        check_response.assert_called_once_with(response)
        self.assertEqual(new_folder, self.folder)

    @patch.object(Folder, '_json_to_folder')
    @patch('pyOutlook.core.folder.check_response')
    @patch('pyOutlook.core.folder.requests.post')
    def test_copy_into(self, post, check_response, json_to_folder):
        new_parent_folder = Folder(self.account, 'Folder1', 'Folder 1', 'Parent Folder', 3, 4, 20)
        response = Mock()
        response.status_code = 200
        response.json.return_value = dict(Id='Folder1',
                                          DisplayName='Folder 1',
                                          ParentFolderId='Parent Folder',
                                          ChildFolderCount=3,
                                          UnreadItemCount=4,
                                          TotalItemCount=20)
        post.return_value = response
        json_to_folder.return_value = self.folder

        new_folder = self.folder.copy_into(new_parent_folder)
        expected_url = 'https://outlook.office.com/api/v2.0/me/MailFolders/ID/copy'
        expected_payload = dict(DestinationId='Folder1')
        post.assert_called_once_with(expected_url, headers=self.folder.headers, data=json.dumps(expected_payload))
        check_response.assert_called_once_with(response)
        self.assertEqual(new_folder, self.folder)

    @patch.object(Folder, '_json_to_folder')
    @patch('pyOutlook.core.folder.check_response')
    @patch('pyOutlook.core.folder.requests.post')
    def test_create_child_folder(self, post, check_response, json_to_folder):
        new_parent_folder = Folder(self.account, 'Folder1', 'Folder 1', 'Parent Folder', 3, 4, 20)
        response = Mock()
        response.status_code = 200
        response.json.return_value = dict(Id='Folder1',
                                          DisplayName='Folder 1',
                                          ParentFolderId='Parent Folder',
                                          ChildFolderCount=3,
                                          UnreadItemCount=4,
                                          TotalItemCount=20)
        post.return_value = response
        json_to_folder.return_value = self.folder

        new_folder = self.folder.create_child_folder('New Child Folder')
        expected_url = 'https://outlook.office.com/api/v2.0/me/MailFolders/ID/childfolders'
        expected_payload = dict(DisplayName='New Child Folder')
        post.assert_called_once_with(expected_url, headers=self.folder.headers, data=json.dumps(expected_payload))
        check_response.assert_called_once_with(response)
        self.assertEqual(new_folder, self.folder)

    @patch.object(Message, '_json_to_messages')
    @patch('pyOutlook.core.folder.check_response')
    @patch('pyOutlook.core.folder.requests.get')
    def test_messages(self, get, check_response, json_to_messages):
        response = Mock()
        response.status_code = 200
        response_json = dict(Id='Folder1',
                             DisplayName='Folder 1',
                             ParentFolderId='Parent Folder',
                             ChildFolderCount=3,
                             UnreadItemCount=4,
                             TotalItemCount=20)
        response.json.return_value = response_json
        get.return_value = response
        json_to_messages.return_value = ['Message 1', 'Message 2']

        messages = self.folder.messages()
        expected_url = 'https://outlook.office.com/api/v2.0/me/MailFolders/ID/messages'
        get.assert_called_once_with(expected_url, headers=self.folder.headers)
        check_response.assert_called_once_with(response)
        self.assertEqual(messages, ['Message 1', 'Message 2'])
        json_to_messages.assert_called_once_with(self.account, response_json)
