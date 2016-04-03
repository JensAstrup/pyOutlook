import requests
import main
import internal_methods


def clean_return_multiple(json):
    """
    :param json:
    :return: list of Folders
    :rtype: list of Folder
    """
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
    def __init__(self, folder_id, folder_name, parent_id, child_folder_count, unread_count, total_items):
        self.parent_id = parent_id
        self.child_folder_count = child_folder_count
        self.unread_count = unread_count
        self.total_items = total_items
        self.name = folder_name
        self.id = folder_id

    def rename_folder(self, new_folder_name):
        access_token = internal_methods.get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id
        payload = '{ "DisplayName": "' + new_folder_name + '"}'

        r = requests.patch(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Renamed folder to: ' + new_folder_name + '. Received the following status code from Outlook: ',
            print r.status_code
            return_folder = r.json()
            return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                          return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                          return_folder['TotalItemCount'])

    def get_subfolders(self):
        access_token = internal_methods.get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id + '/childfolders'

        r = requests.get(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Retrieved folders. Received the following status code from Outlook: ',
            print r.status_code
            return clean_return_multiple(r.json())

    def delete_folder(self):
        access_token = internal_methods.get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id

        r = requests.delete(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Deleted folder: ' + self.name + '. Received the following status code from Outlook: ',
            print r.status_code

    def move_folder(self, destination_folder):
        """
        :param destination_folder: Folder Id
        :return: Folder
        :rtype: Folder
        """
        access_token = internal_methods.get_global_token()
        print access_token
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id + '/move'
        payload = '{ "DestinationId": "' + destination_folder + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Moved folder. Received the following status code from Outlook: ',
            print r.status_code
            return_folder = r.json()
            return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                          return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                          return_folder['TotalItemCount'])

    def copy_folder(self, destination_folder):
        """
        :param destination_folder: Folder Id
        :return: Folder
        :rtype: Folder
        """
        access_token = internal_methods.get_global_token()
        print access_token
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + self.id + '/copy'
        payload = '{ "DestinationId": "' + destination_folder + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

        else:
            print 'Copied folder. Received the following status code from Outlook: ',
            print r.status_code
            return_folder = r.json()
            return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                          return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                          return_folder['TotalItemCount'])


def create_folder(self, parent_id, folder_name):
    """
    :param parent_id:
    :param folder_name:
    :return: Folder
    :rtype: Folder
    """
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + parent_id + '/childfolders'
    payload = '{ "DisplayName": "' + folder_name + '"}'

    r = requests.post(endpoint, headers=headers, data=payload)

    if 399 < r.status_code < 452:
        raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        print 'Created folder: ' + folder_name + '. Received the following status code from Outlook: ',
        print r.status_code
        return_folder = r.json()
        return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                      return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                      return_folder['TotalItemCount'])


def get_folders(self):
    """
    :param self:
    :return: list of Folders
    :rtype: list of Folder
    """
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/'

    r = requests.get(endpoint, headers=headers)

    if 399 < r.status_code < 452:
        raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        return clean_return_multiple(r.json())


def get_folder(self, folder_id):
    """
    :param self:
    :param folder_id:
    :return: Folder
    :rtype: Folder
    """
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + folder_id

    r = requests.get(endpoint, headers=headers)

    if 399 < r.status_code < 452:
        raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        return_folder = r.json()
        return Folder(return_folder['Id'], return_folder['DisplayName'], return_folder['ParentFolderId'],
                      return_folder['ChildFolderCount'], return_folder['UnreadItemCount'],
                      return_folder['TotalItemCount'])

