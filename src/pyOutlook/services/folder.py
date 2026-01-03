import requests

from pyOutlook.internal.utils import check_response

__all__ = ['FolderService']


class FolderService:
    '''Service class for creating Folder instances from API responses.
    
    This service acts as a factory, handling retrieval and instantiation of
    Folder objects. All operations on individual folders are instance methods
    on the Folder class itself.
    '''
    
    @classmethod
    def get_folders(cls, account):
        '''Retrieves all folders for an account.
        
        Args:
            account: OutlookAccount instance
            
        Returns:
            List of Folder instances
        '''
        endpoint = 'https://graph.microsoft.com/v1.0/me/MailFolders/'
        r = requests.get(endpoint, headers=account._headers)
        
        if check_response(r):
            return cls._json_to_folders(account, r.json())
        return []
    
    @classmethod
    def get_folder(cls, account, folder_id: str):
        '''Retrieves a single folder by ID.
        
        Args:
            account: OutlookAccount instance
            folder_id: The ID of the folder to retrieve
            
        Returns:
            Folder instance
        '''
        endpoint = f'https://graph.microsoft.com/v1.0/me/MailFolders/{folder_id}'
        r = requests.get(endpoint, headers=account._headers)
        
        check_response(r)
        return cls._json_to_folder(account, r.json())
    
    @classmethod
    def _json_to_folder(cls, account, json_value: dict):
        '''Factory method: Converts JSON to a Folder instance.
        
        Args:
            account: OutlookAccount instance
            json_value: JSON object representing a folder
            
        Returns:
            Folder instance
        '''
        from pyOutlook.core.folder import Folder
        
        return Folder(
            account, 
            json_value['Id'], 
            json_value['DisplayName'], 
            json_value['ParentFolderId'],
            json_value['ChildFolderCount'], 
            json_value['UnreadItemCount'], 
            json_value['TotalItemCount']
        )
    
    @classmethod
    def _json_to_folders(cls, account, json_value: dict):
        '''Converts JSON array to list of Folder instances.
        
        Args:
            account: OutlookAccount instance
            json_value: JSON response containing 'value' array
            
        Returns:
            List of Folder instances
        '''
        return [cls._json_to_folder(account, folder) for folder in json_value['value']]
