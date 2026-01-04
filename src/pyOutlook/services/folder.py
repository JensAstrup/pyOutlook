from typing import TYPE_CHECKING

import requests

from pyOutlook.internal.utils import check_response
from pyOutlook.core.folder import Folder

if TYPE_CHECKING:
    from core.main import OutlookAccount

__all__ = ['FolderService']


class FolderService:
    '''Service class for creating Folder instances from API responses.
    
    This service acts as a factory, handling retrieval and instantiation of
    Folder objects. All operations on individual folders are instance methods
    on the Folder class itself.
    '''

    account: 'OutlookAccount'

    def __init__(self, account: 'OutlookAccount'):
        self.account = account
    
    def all(self) -> list['Folder']:
        '''Retrieves all folders for an account.
        
        Returns:
            List of Folder instances
        '''
        endpoint = 'https://graph.microsoft.com/v1.0/me/mailFolders/'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        
        if check_response(r):
            return self._json_to_folders(r.json())
        return []
    
    def get(self, folder_id: str) -> 'Folder':
        '''Retrieves a single folder by ID.
        
        Args:
            folder_id: The ID of the folder to retrieve
            
        Returns:
            Folder instance
        '''
        endpoint = f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        
        check_response(r)
        return self._json_to_folder(r.json())
    
    def _json_to_folder(self, json_value: dict) -> 'Folder':
        '''Factory method: Converts JSON to a Folder instance.
        
        Args:
            json_value: JSON object representing a folder
            
        Returns:
            Folder instance
        '''
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
        '''Converts JSON array to list of Folder instances.
        
        Args:
            json_value: JSON response containing 'value' array
            
        Returns:
            List of Folder instances
        '''
        return [self._json_to_folder(folder) for folder in json_value['value']]
