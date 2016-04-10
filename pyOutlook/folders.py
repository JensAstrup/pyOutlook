import requests

from internal import internalMethods
from internal.errors import AuthError


def clean_return_multiple(json):
    return_list = []
    for key in json['value']:
        parent_id = key['ParentFolderId']
        child_folder_count = key['ChildFolderCount']
        unread_count = key['UnreadItemCount']
        total_items = key['TotalItemCount']
        folder_name = key['DisplayName']
        folder_id = key['Id']
        entry = Folder(folder_id, folder_name, parent_id, child_folder_count, unread_count, total_items)
        return_list.append(entry)
    return return_list


class Folder(object):
    """An object representing a Folder in the OutlookAccount provided.

    Attributes:
        folder_id: The static id generated by Outlook to identify this folder.
        folder_name: The name of this folder as displayed in the account
        parent_id: The id of the folder which houses this Folder object
        child_folder_count: The number of child folders inside this Folder
        unread_count: The number of unread messages inside this Folder
        total_items: A sum of all items inside Folder

    """
    def __init__(self, folder_id, folder_name, parent_id, child_folder_count, unread_count, total_items):
        self.parent_id = parent_id
        self.child_folder_count = child_folder_count
        self.unread_count = unread_count
        self.total_items = total_items
        self.name = folder_name
        self.id = folder_id

    def rename_folder(self, new_folder_name):
        """Renames the Folder to the provided name.

        Args:
            new_folder_name: A string of the replacement name.

        Raises:
            AuthError: Raised if Outlook returns a 401, generally caused by an invalid or expired access token.

        Returns:
            A new Folder representing the folder with the new name on Outlook.

        """
        access_token = internalMethods.get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id
        payload = '{ "DisplayName": "' + new_folder_name + '"}'

        r = requests.patch(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Renamed folder to: ' + new_folder_name + '. Received the following status code from Outlook: ',
            print r.status_code
            return_folder = r.json()
            return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                          return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                          return_folder['TotalItemCount'])

    def get_subfolders(self):
        """Retrieve all child Folders inside of this Folder.

        Raises:
            AuthError: Raised if Outlook returns a 401, generally caused by an invalid or expired access token.

        Returns:
            List[Folder]
        """
        access_token = internalMethods.get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id + '/childfolders'

        r = requests.get(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Retrieved folders. Received the following status code from Outlook: ',
            print r.status_code
            return clean_return_multiple(r.json())

    def delete_folder(self):
        """Deletes this Folder.

        Warnings:
            This deletes the folder inside of the account provided - not the Folder object!

        Raises:
            AuthError: Raised if Outlook returns a 401, generally caused by an invalid or expired access token.

        """
        access_token = internalMethods.get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id

        r = requests.delete(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Deleted folder: ' + self.name + '. Received the following status code from Outlook: ',
            print r.status_code

    def move_folder(self, destination_folder):
        """Move the Folder into a different folder.

        This makes the Folder provided a child folder of the destination_folder.

        Raises:
            AuthError: Raised if Outlook returns a 401, generally caused by an invalid or expired access token.

        Args:
            destination_folder: An id, provided by Outlook, specifying the folder that should become the parent

        Returns:
            A new Folder object representing the folder that is now inside of the destination_folder.

        """
        access_token = internalMethods.get_global_token()
        print access_token
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id + '/move'
        payload = '{ "DestinationId": "' + destination_folder + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Moved folder. Received the following status code from Outlook: ',
            print r.status_code
            return_folder = r.json()
            return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                          return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                          return_folder['TotalItemCount'])

    def copy_folder(self, destination_folder):
        """Copies the Folder into the provided destination folder.

        Raises:
            AuthError: Raised if Outlook returns a 401, generally caused by an invalid or expired access token.

        Args:
            destination_folder: A string containing the id of the folder, as provided by Outlook, that this Folder
            should be copied to.

        Returns:
            A new Folder representing the newly created folder.

        """
        access_token = internalMethods.get_global_token()
        print access_token
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id + '/copy'
        payload = '{ "DestinationId": "' + destination_folder + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Copied folder. Received the following status code from Outlook: ',
            print r.status_code
            return_folder = r.json()
            return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                          return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                          return_folder['TotalItemCount'])


def create_folder(self, parent_id, folder_name):
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + parent_id + '/childfolders'
    payload = '{ "DisplayName": "' + folder_name + '"}'

    r = requests.post(endpoint, headers=headers, data=payload)

    if 399 < r.status_code < 452:
        raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        print 'Created folder: ' + folder_name + '. Received the following status code from Outlook: ',
        print r.status_code
        return_folder = r.json()
        return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                      return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                      return_folder['TotalItemCount'])


def get_folders(self):
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/'

    r = requests.get(endpoint, headers=headers)

    if 399 < r.status_code < 452:
        raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        return clean_return_multiple(r.json())


def get_folder(self, folder_id):
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_id

    r = requests.get(endpoint, headers=headers)

    if 399 < r.status_code < 452:
        raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        return_folder = r.json()
        return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                      return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                      return_folder['TotalItemCount'])

