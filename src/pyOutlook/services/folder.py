from typing import TYPE_CHECKING

import requests

from pyOutlook.internal.utils import check_response
from pyOutlook.core.folder import Folder

if TYPE_CHECKING:
    from core.main import OutlookAccount

__all__ = ['FolderService']


class FolderService:
    """Service class for creating Folder instances from API responses.

    This service acts as a factory, handling retrieval and instantiation of
    Folder objects. All operations on individual folders are instance methods
    on the Folder class itself.

    :param account: The OutlookAccount for API authentication.
    :type account: OutlookAccount

    :ivar account: The associated OutlookAccount.
    """

    account: 'OutlookAccount'

    def __init__(self, account: 'OutlookAccount'):
        self.account = account

    def all(self) -> list['Folder']:
        """Retrieve all folders for the account.

        :returns: List of Folder instances.
        :rtype: list[Folder]

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.
        """
        endpoint = 'https://graph.microsoft.com/v1.0/me/mailFolders/'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)

        if check_response(r):
            return self._json_to_folders(r.json())
        return []

    def get(self, folder_id: str) -> 'Folder':
        """Retrieve a single folder by ID.

        :param folder_id: The ID of the folder to retrieve. Can also be a well-known
            folder name like ``'Inbox'``, ``'SentItems'``, ``'DeletedItems'``, ``'Drafts'``.
        :type folder_id: str

        :returns: The requested Folder instance.
        :rtype: Folder

        :raises AuthError: If authentication fails.
        :raises RequestError: If the folder is not found or the request fails.
        """
        endpoint = f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)

        check_response(r)
        return self._json_to_folder(r.json())

    def _json_to_folder(self, json_value: dict) -> 'Folder':
        """Factory method: Convert JSON to a Folder instance.

        :param json_value: JSON object representing a folder.
        :type json_value: dict

        :returns: Folder instance.
        :rtype: Folder
        """
        from pyOutlook.core.folder import Folder

        return Folder(
            self.account,
            json_value['id'],
            json_value['displayName'],
            json_value['parentFolderId'],
            json_value['childFolderCount'],
            json_value['unreadItemCount'],
            json_value['totalItemCount']
        )

    def _json_to_folders(self, json_value: dict) -> list['Folder']:
        """Convert JSON array to list of Folder instances.

        :param json_value: JSON response containing ``'value'`` array.
        :type json_value: dict

        :returns: List of Folder instances.
        :rtype: list[Folder]
        """
        return [self._json_to_folder(folder) for folder in json_value['value']]
