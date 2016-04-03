import requests
import main


class Folder(object):
    def __init__(self, folder_id, folder_name, parent_id, child_folder_count, unread_count, total_items):
        self.parent_id = parent_id
        self.child_folder_count = child_folder_count
        self.unread_count = unread_count
        self.total_items = total_items
        self.folder_name = folder_name
        self.folder_id = folder_id


def create_folder(self, parent_id, folder_name):
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + parent_id + '/childfolders'
    payload = '{ "DisplayName": "' + folder_name + '"}'

    r = requests.post(endpoint, headers=headers, data=payload)

    if 399 < r.status_code < 452:
        raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        print 'Created folder: ' + folder_name + '. Received the following status code from Outlook: ',
        print r.status_code
        return r.json()['Id']


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


def get_folders(self):
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/'

    r = requests.get(endpoint, headers=headers)

    if 399 < r.status_code < 452:
        raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        return clean_return_multiple(r.json())


def get_subfolders(self, parent_folder_id):
    headers = {"Authorization": "Bearer " + self.access_token, "Content-Type": "application/json"}
    endpoint = 'https://outlook.office.com/api/v2.0/me/MailFolders/' + parent_folder_id + '/childfolders'

    r = requests.get(endpoint, headers=headers)

    if 399 < r.status_code < 452:
        raise main.AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    else:
        print 'Copied Message to. Received the following status code from Outlook: ',
        print r.status_code
        print r.json()
